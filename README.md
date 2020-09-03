# cfn-cr-s3-notification-configuration
A cloudformation custom resource to allow adding lambda notifications to an S3 bucket.

Creating a Lambda which subscribes to S3 bucket notifications (create object event) directly
is a pretty common scenario. It sounds trivial to setup however it actually is NOT.  The problem
is that the bucket and the lambda resource contains a circular dependency which makes it
difficult to deploy.

The [official CloudFormation Documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-notificationconfig.html)
states that there is a known circular dependency issue with this use case and the workaround
they suggest is to create all the resources first without specifying the notification configuration.
Then, update the stack with a notification configuration. This means that you would need two
deployment steps to setup a lambda based notiification bucket.

The problem is that there isn't a separate AWS cloudformation resource for
[S3 bucket notification](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-notificationconfig.html).
The [LambdaConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-notificationconfig-lambdaconfig.html)
is part of S3 bucket Notification Config under Bucket resource definition.

This custom resource fixes the problem by providing a separate AWS cloudformation resource for S3
bucket notification.

Inspiration:
- https://aws.amazon.com/premiumsupport/knowledge-center/cloudformation-s3-notification-lambda/
- https://aws.amazon.com/blogs/mt/resolving-circular-dependency-in-provisioning-of-amazon-s3-buckets-with-aws-lambda-event-notifications/

## Development

### Contributions
Contributions are welcome.

### Requirements
Run `pipenv install --dev` to install both production and development
requirements, and `pipenv shell` to activate the virtual environment. For more
information see the [pipenv docs](https://pipenv.pypa.io/en/latest/).

After activating the virtual environment, run `pre-commit install` to install
the [pre-commit](https://pre-commit.com/) git hook.

### Create a local build

```shell script
$ sam build --use-container
```

### Run locally

```shell script
$ sam local invoke HelloWorldFunction --event events/event.json
```

### Run unit tests
Tests are defined in the `tests` folder in this project. Use PIP to install the
[pytest](https://docs.pytest.org/en/latest/) and run unit tests.

```shell script
$ python -m pytest tests/ -v
```

## Deployment

### Build

```shell script
sam build
```

### Deploy Lambda to S3
This requires the correct permissions to upload to bucket
`bootstrap-awss3cloudformationbucket-19qromfd235z9` and
`essentials-awss3lambdaartifactsbucket-x29ftznj6pqw`

```shell script
sam package --template-file .aws-sam/build/template.yaml \
  --s3-bucket essentials-awss3lambdaartifactsbucket-x29ftznj6pqw \
  --output-template-file .aws-sam/build/cfn-cr-s3-notification-configuration.yaml

aws s3 cp .aws-sam/build/cfn-cr-s3-notification-configuration.yaml s3://bootstrap-awss3cloudformationbucket-19qromfd235z9/cfn-cr-s3-notification-configuration/master/
```

### Install Lambda into AWS
Create the following [sceptre](https://github.com/Sceptre/sceptre) file

config/prod/cfn-cr-s3-notification-configuration.yaml
```yaml
template_path: "remote/cfn-cr-s3-notification-configuration.yaml"
stack_name: "cfn-cr-s3-notification-configuration"
stack_tags:
  Department: "Platform"
  Project: "Infrastructure"
  OwnerEmail: "it@sagebase.org"
hooks:
  before_launch:
    - !cmd "curl https://bootstrap-awss3cloudformationbucket-19qromfd235z9.s3.amazonaws.com/cfn-cr-s3-notification-configuration/master/cfn-cr-s3-notification-configuration.yaml --create-dirs -o templates/remote/cfn-cr-s3-notification-configuration.yaml"
```

Install the lambda using sceptre:
```shell script
sceptre --var "profile=my-profile" --var "region=us-east-1" launch prod/cfn-cr-s3-notification-configuration.yaml
```

## Usage

Add the custom resource in your cloud formation template. Here's an example:
```yaml
  AddBucketNotificationConfig:
    Type: Custom::S3NotificationConfiguration
    Properties:
      ServiceToken: !ImportValue
        'Fn::Sub': '${AWS::Region}-cfn-cr-s3-notification-configuration-LambdaConfigurationFunctionArn'
      NotificationBucket: "my-bucket"
      LambdaFunctionArn: "arn:aws:lambda:us-east-1:787179373106:function:cfn-cr-s3-notification-configuration-LambdaConfigurationFunction"
      LambdaNotificationEvents: ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
```

The creation of the custom resource triggers the lambda which will add a notification configuration to
the notification bucket.
