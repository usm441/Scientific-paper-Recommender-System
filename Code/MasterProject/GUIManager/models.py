from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


# Create your models here.

class PaperAuthor(models.Model):
    """
    A relationship table for Paper and Authors
    """
    author_name = models.CharField(max_length=200, unique=True)


class PaperKeyword(models.Model):
    """
    A relationship table for Paper and Keywords obtained from the APIS
    """
    keyword = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.keyword


class PaperTerm(models.Model):
    """
    A relationship table for Paper, its terms and its relevance score
    """
    term = models.CharField(max_length=200, unique=True)
    relevance_score = models.FloatField()

    def __str__(self):
        return self.keyword


class Paper(models.Model):
    """
    Creates a table for Paper Meta data
    """
    # TODO: rename  plurlas
    doc_id = models.IntegerField(default=-1)  # manually maintained doc_id
    url = models.CharField(max_length=255)
    external_id = models.IntegerField(null=True) # for the bootstrapped papers (citulike_id)
    published_date = models.DateField(null=True)
    journal_name = models.CharField(max_length=400, null=True)
    title = models.CharField(max_length=255, unique=True) # add unique
    abstract = models.TextField()
    authors = models.ManyToManyField(PaperAuthor)
    keywords = models.ManyToManyField(PaperKeyword)
    terms = models.ManyToManyField(PaperTerm)

    def __str__(self):
        return self.title

    def validate_unique(self, *args, **kwargs):
        # method overridden to handle exception for inserting multiple papers
        try:
            super(Paper, self).validate_unique(*args, **kwargs)
        except ValidationError as e:
            print('Not unique title')
            return False

        return True


class MyCatalog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    papers = models.ManyToManyField(Paper)

    def __str__(self):
        return self.user.username


class Algorithm(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    in_use = models.BooleanField()
    is_ready = models.BooleanField(default=True)
    is_update_of = models.ForeignKey("self", null=True, blank=True)


class Recommendation(models.Model):
    """
    Details on each user recommendation
    """
    algorithm = models.ForeignKey(Algorithm, on_delete=models.CASCADE)
    # Allow log entry deletion only when Recommendation Algo. is deleted
    # User deletion should not affect this table. Evaluation metrics shall run for each entry here
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    input_rating_count=models.BigIntegerField()
    created_date = models.DateTimeField(auto_now_add=True)


class RecommendationResult(models.Model):
    """
    Details on the papers recommended for every user query
    """

    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE)
    predicted_score = models.FloatField()
    predicted_rank = models.SmallIntegerField()
    prediction_type = models.CharField(max_length=200, null=True)
    is_clicked = models.NullBooleanField(null=True)
    # REfit_cycle to be used in Coverage calculation
    Refit_cycle = models.IntegerField(null=True)


class UserFeedback(models.Model):
    """
    Storing the feedback of a user for each recommended paper
    """
    # Allow field to be null because a user can add a paper to his catalog from search.
    # Search results do not have any recommendation id tied to them.
    recommendationresult_detail = models.OneToOneField(RecommendationResult, on_delete=models.CASCADE, null=True)
    user_rating = models.SmallIntegerField()
    feedback_type = models.CharField(max_length=10)
    datetime = models.DateTimeField(auto_now_add=True)

# TODO Explore the possiblity of keeping all metrics in a separate table
# TODO Change this to a OnetoONe relation on recommendation from one2many
class EvaluationMetric(models.Model):
    """
    Storing metrics like Precision,Rank for each user query
    """
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE)
    p_at_10 = models.FloatField()
    p_at_20 = models.FloatField(null=True)
    p_at_30 = models.FloatField(null=True)
    p_at_40 = models.FloatField(null=True)
    p_at_50 = models.FloatField(null=True)
    ndcg_at_10 = models.FloatField()
    ndcg_at_20 = models.FloatField(null=True)
    ndcg_at_30 = models.FloatField(null=True)
    mrr_at_10 = models.FloatField()
    mrr_at_20 = models.FloatField(null=True)
    mrr_at_30 = models.FloatField(null=True)
    ctr = models.FloatField(null=True)

class SystemRecommendations(models.Model):
    """
    Store the Algorithm configured as system Default Recommendation
    """

    algorithm = models.ForeignKey(Algorithm, on_delete=models.CASCADE)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    comments = models.CharField(max_length=500)
    isactive = models.BooleanField(default=True)


class UserMapping(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    external_hash = models.CharField(max_length=200, null=True)
    external_user_id = models.IntegerField()


class RatingMatrix(models.Model):
    """
        Contains Ratings from MyCAtalog and UserFeedback
        any paper added to my_catalog will be available here
        or when the admin converts feedback to ratings then also the below table
        gets populated
    """
    user_map = models.ForeignKey(UserMapping, on_delete=models.CASCADE, default=-1)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    doc_id = models.IntegerField()
    external_user_id = models.IntegerField()
    rating = models.SmallIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)


class PaperLDATheta(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.SET_NULL, null=True)
    topic_id = models.IntegerField()
    doc_id = models.IntegerField()
    value = models.FloatField()

    def __str__(self):
        return "{}  {}  {}".format(self.doc_id, self.topic_id, self.value)

class Vocabulary(models.Model):
    term_id = models.IntegerField(primary_key=True)
    term = models.CharField(max_length=100)

class SystemAlgorithmRecommendationLog(models.Model):
    system_algorithm = models.ForeignKey(SystemRecommendations,on_delete=models.CASCADE)
    recommendation = models.OneToOneField(Recommendation, on_delete=models.CASCADE)

