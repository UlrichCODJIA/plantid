#!/bin/bash

# 0. Basic Setup
#########################

# Experiment directory
expdir=exp/train_nodev_transformer_fongbe
# Data directory
datadir=data/train

# Kaldi stage
stage=0

. ./path.sh
. ./cmd.sh

# Specify GPU usage
. utils/parse_options.sh || exit 1
if [ $# -ne 0 ]; then
    echo "Error: No positional arguments are required."
    exit 2
fi

# 1. Data Preparation (if needed)
#########################

if [ $stage -le 0 ]; then
    # Prepare data for each set (train, test)
    for x in train test; do
        # Create CSV files for Kaldi data preparation
        python3 scripts/kaldi2deepSpeech_importer.py data/$x/wav data/$x/text $x
        # Extract transcripts from the CSV files
        cut -d "," -f 3 data/$x.csv | sed '1d' >data/$x/text
        # Remove unnecessary DeepSpeech.py CSV files
        rm data/$x.csv
    done
fi

# 2. Feature Extraction & Data Processing
#########################

# Feature parameters
nj=10 # Number of parallel jobs
fbank_conf=conf/fbank.conf
cmvn_opts="--norm-means=true --norm-vars=true"
do_delta=false

# Check CUDA availability
if ! cuda-compiled; then
    cat >&2 <<EOF
    CUDA is not installed.
    You need to install CUDA in order to run ESPnet.
EOF
    exit 1
fi

# Set CUDA_VISIBLE_DEVICES
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}

# Prepare dictionary
mkdir -p data/lang_1char/
echo "<unk> 1" >data/lang_1char/words.txt
python3 -c "import json; print('\n'.join([f'{k} {i+2}' for k, i in json.load(open('data/local/char_map.json', 'r')).items()]))" >>data/lang_1char/words.txt
utils/sym2int.pl <data/lang_1char/words.txt --space " " >data/lang_1char/words.int
echo "sil" >data/lang_1char/silence_phones.txt
echo "sil" >data/lang_1char/optional_silence.txt
cut -d " " -f 2- data/local/dict/lexicon.txt | tr ' ' '\n' | sort -u | grep -v -e 'sil' >data/lang_1char/nonsilence_phones.txt
cp -r data/lang_1char data/lang_1char_tmp
utils/prepare_lang.sh data/lang_1char_tmp "<unk>" data/local/lang_tmp data/lang
utils/validate_lang.pl data/lang

# Feature extraction and data processing
if [ $stage -le 1 ]; then
    # Make a development set
    utils/subset_data_dir.sh --first data/train 1000 data/dev # 1000 utts for dev

    for set in train dev test; do
        # 1. Feature extraction
        steps/make_fbank_pitch.sh --cmd "$train_cmd" --nj $nj \
            --write-utt2num-frames true \
            data/$set $expdir/log/fbank/$set $expdir/fbank/$set
        steps/compute_cmvn_stats.sh data/$set $expdir/log/fbank/$set $expdir/fbank/$set
        # 3. Remove problematic utterances
        utils/fix_data_dir.sh data/$set
        # 4. Compute global CMVN stats
        #compute-cmvn-stats scp:data/$set/feats.scp data/cmvn.ark
        # 5. Apply global CMVN and add deltas
        steps/apply_cmvn.sh --cmd "$train_cmd" $cmvn_opts data/$set $expdir/fbank/$set $expdir/fbank_cmvn/$set
        if [ $do_delta == "true" ]; then
            steps/compute_deltas.sh --cmd "$train_cmd" $cmvn_opts data/$set \
                $expdir/log/deltas/$set $expdir/deltas/$set
        fi
    done

    # Dump features for ESPnet
    dump.sh --cmd "$train_cmd" --nj $nj --do_delta $do_delta \
        data/train data/cmvn.ark $expdir/dump/train $expdir/dump/train/delta${do_delta}
    dump.sh --cmd "$train_cmd" --nj $nj --do_delta $do_delta \
        data/dev data/cmvn.ark $expdir/dump/dev $expdir/dump/dev/delta${do_delta}
    dump.sh --cmd "$train_cmd" --nj $nj --do_delta $do_delta \
        data/test data/cmvn.ark $expdir/dump/test $expdir/dump/test/delta${do_delta}
fi

# 3. Training Configuration
#########################

# Training config file
fongbe_train_config=conf/tuning/train_pytorch_transformer.yaml
# Training and validation JSON files
fongbe_train_json=dump/train/delta${do_delta}/data.json
fongbe_valid_json=dump/dev/delta${do_delta}/data.json

# 4. Model Training
#########################

# Training with PyTorch
if [ $stage -le 2 ]; then
    mkdir -p $expdir
    resume=$([ ! -f $expdir/results/snapshot.ep.last ] && echo "" || echo "--resume $expdir/results/snapshot.ep.last")
    # Set up training command
    $cuda_cmd $expdir/log/train.log \
        espnet/bin/asr_train.py \
        --config $fongbe_train_config \
        --ngpu $ngpu \
        --backend pytorch \
        --outdir $expdir/results \
        --tensorboard-dir tensorboard/${expdir} \
        --debugmode 1 \
        --dict data/lang_1char/train_nodev_char_units.txt \
        --debugdir $expdir \
        --minibatches 0 \
        --verbose 1 \
        --resume $resume \
        --train-json $fongbe_train_json \
        --valid-json $fongbe_valid_json
fi

# 5. Decoding
#########################
if [ $stage -le 3 ]; then
    # Set paths
    pids=() # initialize process IDs
    for set in dev test; do
        (
            decode_dir=decode_${set}_$(basename ${fongbe_train_config%.*})
            feat_recog_dir=$expdir/${decode_dir}/data_${do_delta}

            # Feature extraction for recognition
            steps/make_fbank_pitch.sh --cmd "$train_cmd" --nj $nj \
                --write-utt2num-frames true \
                data/$set $expdir/log/fbank/$set $feat_recog_dir
            steps/compute_cmvn_stats.sh data/$set $expdir/log/fbank/$set $feat_recog_dir

            # Apply global CMVN and add deltas
            steps/apply_cmvn.sh --cmd "$train_cmd" $cmvn_opts data/$set $expdir/fbank/$set $feat_recog_dir
            if [ $do_delta == "true" ]; then
                steps/compute_deltas.sh --cmd "$train_cmd" $cmvn_opts data/$set \
                    $expdir/log/deltas/$set $feat_recog_dir
            fi

            # Dump json file
            dump.sh --cmd "$train_cmd" --nj $nj --do_delta $do_delta \
                data/$set data/cmvn.ark $expdir/dump/$set $expdir/${decode_dir}/data
        ) &
        pids+=($!) # store background pids
    done
    i=0
    for pid in "${pids[@]}"; do wait ${pid} || ((++i)); done
    [ $i -gt 0 ] && echo "$0: ${i} background jobs are failed." && false
    echo "Finished"
fi

# 6. Scoring
#########################
if [ $stage -le 4 ]; then
    for set in dev test; do
        decode_dir=decode_${set}_$(basename ${fongbe_train_config%.*})
        echo "WER on $set:"
        # Compute WER
        $decode_cmd --mem 4G --max-active=7000 $expdir/log/wer_${set}.log \
            asr_recog.py \
            --config $fongbe_train_config \
            --ngpu $ngpu \
            --backend pytorch \
            --debugmode 1 \
            --dict data/lang_1char/train_nodev_char_units.txt \
            --result-label $expdir/${decode_dir}/data.json \
            --model $expdir/results/model.last10.avg.best \
            --rnnlm LM/fongbe.arpa
        # Show results
        tail -n 1 $expdir/log/wer_${set}.log
    done
fi
