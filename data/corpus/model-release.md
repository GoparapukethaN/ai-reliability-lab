# Model release runbook

Model releases should start with an offline evaluation report. The report should include
the candidate model version, baseline version, dataset window, metrics, and known failure
cases.

## Promotion

A candidate can be promoted only after evaluation, smoke tests, and owner review pass.
The model registry should keep the candidate, current stable version, and previous stable
version visible.

## Rollback

When live metrics regress, roll back by moving the registry alias to the previous stable
model. Rollback should not require retraining. The release owner should record the
triggering metric, time of rollback, and follow-up action.

