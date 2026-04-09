from django.contrib.gis.db import models


class GeographicScope(models.TextChoices):
    LOCAL = "local"
    STATE = "state"
    REGIONAL = "regional"
    NATIONAL = "national"
    MULTINATIONAL = "multinational"
    GLOBAL = "global"


class EngagementType(models.TextChoices):
    VOLUNTEER_IN_PERSON = "volunteer_in_person"
    VOLUNTEER_REMOTE = "volunteer_remote"
    DONATE_ONE_TIME = "donate_one_time"
    DONATE_RECURRING = "donate_recurring"
    ADVOCACY = "advocacy"
    EDUCATION = "education"
    CAREER = "career"
    CITIZEN_SCIENCE = "citizen_science"


class TimeCommitment(models.TextChoices):
    MINUTES = "minutes"
    HOURS_PER_WEEK = "hours_per_week"
    DAYS_PER_MONTH = "days_per_month"
    FLEXIBLE = "flexible"
    EVENT_BASED = "event_based"


class AIRecommendation(models.TextChoices):
    INCLUDE = "include"
    EXCLUDE = "exclude"


class ReviewStatus(models.TextChoices):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
