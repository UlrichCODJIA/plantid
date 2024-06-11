import json
from app.extensions import events, lambda_client


# Function to create CloudWatch event rule
def create_cloudwatch_rule(object_key, lambda_function_name, delay_minutes=10):
    # Create a unique rule name
    rule_name = f"delete_{object_key.replace('/', '_')}"

    # Create the rule
    response = events.put_rule(
        Name=rule_name,
        ScheduleExpression=f"rate({delay_minutes} minutes)",
        State="ENABLED",
    )

    # Add the Lambda function as the target
    target_id = "1"
    lambda_arn = lambda_client.get_function(FunctionName=lambda_function_name)[
        "Configuration"
    ]["FunctionArn"]
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

    # Grant the necessary permissions to CloudWatch to invoke the Lambda function
    lambda_client.add_permission(
        FunctionName=lambda_function_name,
        StatementId=f"{rule_name}_invoke_permission",
        Action="lambda:InvokeFunction",
        Principal="events.amazonaws.com",
        SourceArn=response["RuleArn"],
    )
