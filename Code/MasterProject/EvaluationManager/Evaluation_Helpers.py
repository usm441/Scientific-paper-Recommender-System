import GUIManager.models as model
import Helpers.Metrics as metrics
from django.db.models import Avg
import Helpers.db_helper as DB
from random import randint
import re as re


def add_recommendation(reclog, recommendations,is_system):
    '''
    insert the recommendations from an algorithm into Recommendation Result Table
    :param reclog: object from recommendation model
    :param recommendations: List of recommendations
    :return:
    '''
    # iterate through all recommendations and add them into the Result Table
    for i in recommendations:
        entry = model.RecommendationResult(predicted_rank=i[0]
                                           , predicted_score=i[2]
                                           , paper=i[1]
                                           , prediction_type=None
                                           , Refit_cycle=None
                                           , recommendation=reclog)
        entry.save()
    if is_system :
        sr=model.SystemRecommendations.objects.get(pk=is_system)
        sar= model.SystemAlgorithmRecommendationLog(system_algorithm=sr,recommendation=reclog)
        sar.save()
    return len(reclog.recommendationresult_set.reverse())


# Method to be deleted once below function is implemented in Algorithm Manager
def get_recommendations(userid, algoid):
    count = model.Paper.objects.all().count()
    rec_set=[model.Paper.objects.get(pk=randint(1, count-1)) for i in range(0,50)]
    recommendations = []
    for i, j in enumerate(rec_set):
        # user = userid
        rank = i + 1
        paper = j
        score = 99 - i
        recommendations.append([rank, paper,score])
    return recommendations


def get_avg_rating(user_id):
    """
    returns average rating of a user based on all rated papers
    Assumption:  Since the system automatically inserts the feedback for a paper
    already rated by a user.We only need to check the paper ratings of the last recommendation
    of the user .The last recommendation will contain existing feedback ratings and
    any new feedback given by user.
    :param user_id:
    :return: Float

    """
    last_rec_id = model.Recommendation.objects \
        .filter(id=user_id) \
        .order_by('created_date').first()

    # perform reverse mapping from userfeedback to get all explicit ratings for the
    # latest recommendation to the user (based on recommendation id)
    average = model.UserFeedback.objects \
        .filter(recommendationresult_detail__recommendation=last_rec_id) \
        .filter(feedback_type='explicit') \
        .aggregate(Avg('user_rating'))

    # return default value of 3 if user has not rated any papers yet
    if average['user_rating__avg'] is None:
        return 3
    else:
        return average['user_rating__avg']


def get_paper_ratings(user_id):
    """
    returns the explicit paper ratings.
    Get the Userfeedback for a user using a reverse lookup in DJango
    :param user_id:
    :return: Dict of paper_id ,rating
    """
    all_feedbacks = model.UserFeedback \
        .objects \
        .filter(recommendationresult_detail__recommendation__user__id=user_id)

    # Check if previous recommendation or ratings exist for the user
    if all_feedbacks is None:
        return None

    paper_ratings = {}
    # get corresponding paper_ids and ratings
    for feedback in all_feedbacks:
        if feedback.feedback_type == 'explicit':
            # get paper_id and rating from its parent table
            paper_ratings[feedback.recommendationresult_detail.paper.id] = feedback.user_rating

    return paper_ratings


def process_user_recommendations(recommendationlog_entry):
    """
    Return a dictionary of formatted results for a recommendation_id
    :param recommendationlog_entry: <class Recommendation>
    :return:
    """
    result_list = []
    # Resultset of all the papers recommended
    results = recommendationlog_entry.recommendationresult_set.all()

    # REsult set of all papers within user's catalog
    users_catalog = recommendationlog_entry.user.mycatalog_set.all()
    users_catalog_set = [i.id for i in users_catalog]

    # Result set of all explicitly rated papers by the user

    user_explicit_ratings = get_paper_ratings(recommendationlog_entry.user.id)

    # Code to insert existing rating feedback of user corresponding to current query
    for result in results:
        rating = 0
        if user_explicit_ratings is not None:
            # check if user has already rated the paper explicitly
            # by checking in user_explicit_rating dictionary
            if result.paper_id in user_explicit_ratings:
                rating = user_explicit_ratings[result.paper_id]

        # check if paper is part of user catalog
        incatalog = 'Yes' if users_catalog.filter(papers=result.paper).exists() else 'No'

        result_dict = {'result_id': result.id
                        , 'rank': result.predicted_rank
                        , 'paper_id': result.paper.id
                        , 'paper_title': result.paper.title
                        , 'paper_abstract': result.paper.abstract
                        , 'paper_url': result.paper.url
                        , 'rating': rating
                        , 'in_catalog': incatalog
                       }
        result_list.append(result_dict)

    return result_list


def add_metrics(page, recommendation):
    """
        Update UserFeedback based on page no. for which feedback was submitted
        and the recommendation object.
        corner case: user doesnt submit feedback for previous pages
        :param recommendation: <class Recommendation>
        :return:
    """
    # this object will have the ground truth and related metrics
    # based on latest feedback
    query_metrics = metrics.Metrics(recommendation)

    # make the initial entries if none has ben made
    if not model.EvaluationMetric.objects.filter(recommendation=recommendation.id).exists():
        evalmetric = model.EvaluationMetric(
            recommendation=recommendation
            , p_at_10=query_metrics.precision_k(10)
            , mrr_at_10=query_metrics.mrr(10)
            , ndcg_at_10=query_metrics.NDCG(10)
        )
        evalmetric.save()
        # assign to metric_entry for use in subsequent code

    metric_entry = model.EvaluationMetric.objects.get(recommendation=recommendation.id)
    # start the loop from 2,since metrics from page 1 are already created
    for i in range(1, int(page) + 1):
        metric_columnname_precision = 'p_at_' + str(i * 10)
        metric_columnname_mrr = 'mrr_at_' + str(i * 10)
        metric_columnname_ndcg = 'ndcg_at_' + str(i * 10)
        setattr(metric_entry, metric_columnname_precision, query_metrics.precision_k(i * 10))
        setattr(metric_entry, metric_columnname_mrr, query_metrics.mrr(i * 10))
        setattr(metric_entry, metric_columnname_ndcg, query_metrics.NDCG(i * 10))
    metric_entry.save()
    return 1


def add_feedback(form_data, user_id):
    recommendation_id = form_data['recommendation_id']
    recommendation_object = model.Recommendation.objects.get(id=recommendation_id)
    user = model.User.objects.get(id=user_id)
    catalog_changes = {}
    relevance_feedback = {}
    # separate the catalog updates and relevance feedback from the form data
    for i in form_data.keys():
        if i.startswith('Catalog'):
            catalog_key = i[8:]
            catalog_changes[catalog_key] = form_data.get(i)
        if i.startswith('relevance'):
            relevance_key = i[10:]
            relevance_feedback[relevance_key] = form_data.get(i)

    # add evaluation feedback
    for key, value in relevance_feedback.items():
        rec_result_object = model.RecommendationResult.objects.get(id=key)
        if not model.UserFeedback.objects \
                .filter(recommendationresult_detail=rec_result_object.id).exists():
            feedback = model.UserFeedback(
                                          recommendationresult_detail=rec_result_object,
                                          # by default value is expected to be 1
                                          user_rating=value,
                                          feedback_type='explicit')
            feedback.save()
        else:
            rec_result_object.userfeedback.user_rating = value
            rec_result_object.userfeedback.save()

    # addition to usercatalog
    for key, value in catalog_changes.items():
        paper = model.RecommendationResult.objects.get(id=key).paper
        '''updating catalog :call function xposed by PaperManager'''
        DB.add_paper_to_catalog(paper, user_id)

        # also add implicit rating
        if not model.UserFeedback.objects \
                .filter(recommendationresult_detail=key) \
                .exists():
            rec_result_object = model.RecommendationResult.objects.get(id=key)
            feedback = model.UserFeedback(
                                            recommendationresult_detail=rec_result_object,
                                            # by default value is expected to be 1
                                            user_rating=1,
                                            feedback_type='implicit')
            feedback.save()
            # TODO Discuss if necessary

    # adding metrics for the feedback
    page = form_data['page']
    add_metrics(page, recommendation_object)

    return 0


def update_ctr(result, page, for_pagination=False):
    '''
    CTR= no of clicks / no of results seen by user
    update the is_clicked property of each recommendation result and then
    count the number of clicked results vs the page being viewd by user.
    when for_pagination is True result should be recommendation id
    :param for_pagination:
    :param result:
    :param page:
    :return:
    '''
    if for_pagination is False:
        # 1. update the isclicked field
        result_obj = model.RecommendationResult.objects.get(pk=result)
        result_obj.is_clicked = True
        result_obj.save()

        # 2. calculate new CTR
        result_count = int(page) * 10
        total_seen = result_obj.recommendation \
            .recommendationresult_set \
            .filter(predicted_rank__lte=result_count)
        clicks = total_seen.filter(is_clicked=True)
        # 3. update or create the evaluation metric
        '''change to get_CTR(recommendation)'''
        metric_object, created = result_obj.recommendation \
            .evaluationmetric_set \
            .get_or_create(defaults={
                                    'p_at_10': 0,
                                    'ndcg_at_10': 0,
                                    'mrr_at_10': 0})
        new_ctr = len(clicks) / len(total_seen)
        # change to update_CTR(ctr,recommendation)
        metric_object.ctr = new_ctr
        metric_object.save()

        return 1
    else:
        # things to do when a new page is shown to user
        # update CTR metrics as denominator of formula has changed
        # 1. calculate new CTR
        result_count = int(page) * 10
        result_obj = model.Recommendation.objects.get(pk=result)
        total_seen = result_obj.recommendationresult_set \
                               .filter(predicted_rank__lte=result_count)
        clicks = total_seen.filter(is_clicked=True)
        # 3. update or create the evaluation metric
        '''change to get_CTR(recommendation)'''
        metric_object, created = result_obj \
            .evaluationmetric_set \
            .get_or_create(defaults={
                                    'p_at_10': 0,
                                    'ndcg_at_10': 0,
                                    'mrr_at_10': 0})
        new_ctr = len(clicks) / len(total_seen)
        # change to update_CTR(ctr,recommendation)
        metric_object.ctr = new_ctr
        metric_object.save()

        return 0


def get_rating_matrix_size():
    return model.RatingMatrix.objects.count()

def set_system_recommendation(user,algo_id,comments=None):
    actalgos=model.SystemRecommendations.objects.filter(isactive=True)
    for i in actalgos:
        i.isactive=False
        i.save()

    if algo_id is not "":
        new_system_algo = model.Algorithm.objects.get(pk=int(algo_id))
        model.SystemRecommendations.objects.create(algorithm=new_system_algo,
                                               modified_by=user,
                                               comments=comments,
                                               isactive=True)
def get_rated_papers(user):
    positive_recs=model.RecommendationResult.objects.filter(userfeedback__user_rating=1,
                                                     recommendation__user=user)

    return [i.paper for i in positive_recs]
