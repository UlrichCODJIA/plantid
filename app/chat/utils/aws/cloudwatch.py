import json
import re

from app.extensions import events, lambda_client


# Function to create CloudWatch event rule
def create_cloudwatch_rule(object_key, lambda_function_name, delay_minutes=10):
    sanitized_key = re.sub(r"[^a-zA-Z0-9-_]", "_", object_key)
    print("sanitized_key is: ", sanitized_key)
    rule_name = f"delete_{sanitized_key}"[:64]
    print("rule_name is: ", rule_name)
    statement_id = f"{rule_name}_invoke_permission"[:100]
    print("statement_id is: ", statement_id)

    response = events.put_rule(
        Name=rule_name,
        ScheduleExpression=f"rate({delay_minutes} minutes)",
        State="ENABLED",
    )

    target_id = "1"
    lambda_arn = lambda_client.get_function(FunctionName=lambda_function_name)["Configuration"]["FunctionArn"]
    events.put_targets(
        Rule=rule_name,
        Targets=[
            {
                "Id": target_id,
                "Arn": lambda_arn,
                "Input": json.dumps({"object_key": object_key}),
            }
        ],
    )

    lambda_client.add_permission(
        FunctionName=lambda_function_name,
        StatementId=statement_id,
        Action="lambda:InvokeFunction",
        Principal="events.amazonaws.com",
        SourceArn=response["RuleArn"],
    )
