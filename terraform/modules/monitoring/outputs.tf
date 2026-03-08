output "alb_logs_bucket" {
  description = "Name of the S3 bucket for ALB logs"
  value       = aws_s3_bucket.alb_logs.bucket
}

output "vpc_flow_logs_group" {
  description = "Name of the CloudWatch log group for VPC flow logs"
  value       = aws_cloudwatch_log_group.vpc_flow_log_group.name
}

output "budget_info" {
  description = "Budget configuration summary"
  value       = "Monthly budget alert of $$${aws_budgets_budget.monthly.limit_amount} set with notifications at 70%, 90%, and forecast thresholds to ${var.alert_email}"
}

output "cost_anomaly_monitor_arn" {
  description = "ID/ARN of the cost anomaly monitor (awscc provider uses id attribute for ARNs)"
  value       = awscc_ce_anomaly_monitor.project_anomaly_monitor.id
}

output "cost_anomaly_subscription_arn" {
  description = "ID/ARN of the cost anomaly subscription (awscc provider uses id attribute for ARNs)"
  value       = awscc_ce_anomaly_subscription.project_anomaly_subscription.id
}

output "cost_anomaly_sns_topic_arn" {
  description = "ARN of the SNS topic for cost anomaly alerts"
  value       = aws_sns_topic.cost_anomaly_alerts.arn
}

output "budget_alerts_sns_topic_arn" {
  description = "ARN of the SNS topic for budget alerts"
  value       = aws_sns_topic.budget_alerts.arn
}
