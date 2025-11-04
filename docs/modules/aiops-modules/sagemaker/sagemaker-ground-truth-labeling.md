# SageMaker Ground truth labeling

**Category:** Sagemaker  
**Module:** `sagemaker/sagemaker-ground-truth-labeling`

## Description

This module creates a workflow for labeling data using SageMaker ground truth.

A bucket is created to store the raw data. Data uploaded to the S3 bucket is then sent to a created SQS queue. If a text job type is selected the contents of `.txt` files uploaded to the bucket is sent to the SQS queue, instead of the file location. A step function is created that runs on a schedule, pulling the unlabeled data from the SQS queue. The function then runs a labeling job, followed by a verification job (only on supported job types, see below) to increase the accuracy of the labeling. Labeled items that fail validation are returned to the SQS queue for relabelling. New labels are then saved to a created Sagemaker feature group.

This module assumes that uploaded content will be free of `Personally Identifiable Information (PII)` and `Adult content`. If this is not the case please remove the appropiate content classifiers from the `create_labeling_job` method.

## Input Parameters

#### Required

- `job-name`: Used as prefix for created resources and executions of workflow
- `task-type`: The labeling task type to be carried out (read more [here](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-task-types.html)). Currently this module supports all built in task types for images and text. 
Allowed values are:
  - [`image_bounding_box`](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-bounding-box.html)
  - [`image_semantic_segmentation`](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-semantic-segmentation.html)
  - [`image_single_label_classification`](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-image-classification.html)
  - [`image_multi_label_classification`](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-image-classification-multilabel.html)
  - [`text_single_label_classification`](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-text-classification.html)
  - [`text_multi_label_classification`](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-text-classification-multilabel.html)
  - [`named_entity_recognition`](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-named-entity-recg.html)
- `labeling-workteam-arn` - ARN of the workteam to carry out the labeling task, can be public or private
  - `labeling-task-price` - Required if public team is to be used
- `labeling-instructions-template-s3-uri` - S3 URI of the labeling template `.html` or `.liquid` file
  - Required for all labeling types _except_ `named_entity_recognition`
- `labeling-categories-s3-uri` - S3 URI of the labeling categories `.json` file
- `labeling-task-title`
- `labeling-task-description`
- `labeling-task-keywords`

For job types supporting verification, currently `image_bounding_box` and `image_semantic_segmentation` further additional fields are required

- `verification-workteam-arn` - ARN of the workteam to carry out the verification task, can be public or private
  - `verification-task-price` - Required if public team is to be used
- `verification-instructions-template-s3-uri` - S3 URI of the verification template `.html` or `.liquid` file
- `verification-categories-s3-uri` - S3 URI of the verification categories `.json` file. The first label must be the label to pass validation, all other labels are validation failures.
- `verification-task-title`
- `verification-task-description`
- `verification-task-keywords`

For more information and examples of the templates please look at the examples. There are also multiple templates available [here](https://github.com/aws-samples/amazon-sagemaker-ground-truth-task-uis/tree/master).

Labeling and verification task title, description and keywords are used to create the task config which will be sent to the human carrying out the labeling or verification job.

More information on using a public workforce like Amazon Mechanical Turk is available [here](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-workforce-management-public.html). Labeling and verification task prices is specified in USD, see [here](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_PublicWorkforceTaskPrice.html) for allowed values. [This page](https://aws.amazon.com/sagemaker/groundtruth/pricing/) provides suggested pricing based on task type.

## Outputs

- `DataStoreBucketName`: Name of the created S3 bucket where the user will upload the raw data
- `DataStoreBucketArn`: ARN of the created S3 bucket where the user will upload the raw data
- `SqsQueueName`: Name of the created SQS queue
- `SqsQueueArn`: ARN of the created SQS queue
- `SqsDlqName`: Name of the created SQS DLQ
- `SqsDlqArn`: ARN of the created SQS DLQ
- `LabelingStateMachineName`: Name of the labeling state machine
- `LabelingStateMachineArn`: ARN of the labeling state machine
- `FeatureGroupName`: Name of the feature group

## Source

[View on GitHub](https://github.com/awslabs/aiops-modules/tree/main/modules/sagemaker/sagemaker-ground-truth-labeling)
