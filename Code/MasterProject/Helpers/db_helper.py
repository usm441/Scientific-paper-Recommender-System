import GUIManager.models as model
import Helpers.Metrics as metrics
from django.db.models import Avg
from django.db.models import Count
from django.db.models import Max
from django.utils import timezone
from Helpers import utilities as utils
# unified script for all database interactions


'''
Methods for EValuation Manager

'''
def get_feedback_ratings():
    #TODO records later than the last inserted record in rating matrix
    return model.Algorithm.objects.annotate(ratings=Count("recommendation__recommendationresult__userfeedback"))

def get_metrics_systemrecommendations(metric_name):
    if metric_name=="precision":
        # Build an annotated queryset
        # p will contain a list of objects with property algorithm name and p_10,p_20 etc
        p= model.SystemAlgorithmRecommendationLog.objects.annotate(p_10= Avg("recommendation__evaluationmetric__p_at_10"),
                                            p_20=Avg("recommendation__evaluationmetric__p_at_20"),
                                            p_30=Avg("recommendation__evaluationmetric__p_at_30"),
                                            p_40=Avg("recommendation__evaluationmetric__p_at_40"),
                                            p_50=Avg("recommendation__evaluationmetric__p_at_50"))
        precision = {}
        for i in p:
            key= i.system_algorithm.algorithm.name+'-' + str(i.system_algorithm.id)
            value= [i.p_10,i.p_20,i.p_30,i.p_40,i.p_50]
            precision[key]=value

        return precision
    elif metric_name=="mrr":
        p= model.SystemAlgorithmRecommendationLog.objects.annotate(mrr_10= Avg("recommendation__evaluationmetric__mrr_at_10"),
                                            mrr_20=Avg("recommendation__evaluationmetric__mrr_at_20"),
                                            mrr_30=Avg("recommendation__evaluationmetric__mrr_at_30"),
                                           )
        mrr = {}
        for i in p:
            key = i.system_algorithm.algorithm.name + '-' +  str(i.system_algorithm.id)
            value= [i.mrr_10,i.mrr_20,i.mrr_30]
            mrr[key]=value

        return mrr
    elif metric_name=="ndcg":
        p= model.SystemAlgorithmRecommendationLog.objects.annotate(ndcg_10= Avg("recommendation__evaluationmetric__ndcg_at_10"),
                                            ndcg_20=Avg("recommendation__evaluationmetric__ndcg_at_20"),
                                            ndcg_30=Avg("recommendation__evaluationmetric__ndcg_at_30"),
                                            )
        ndcg = {}
        for i in p:
            key = i.system_algorithm.algorithm.name + '-' + str(i.system_algorithm.id)
            value= [i.ndcg_10,i.ndcg_20,i.ndcg_30]
            ndcg[key]=value

        return ndcg
    elif metric_name=="ctr":
        p= model.SystemAlgorithmRecommendationLog.objects.annotate(ctr= Avg("recommendation__evaluationmetric__ctr"))
        ctr = {}
        for i in p:
            key = i.system_algorithm.algorithm.name + '-' +  str(i.system_algorithm.id)
            value= i.ctr
            ctr[key]=value

        return ctr

def get_metrics(metric_name):
    if metric_name=="precision":
        # Build an annotated queryset
        # p will contain a list of objects with property algorithm name and p_10,p_20 etc
        p= model.Algorithm.objects.annotate(p_10= Avg("recommendation__evaluationmetric__p_at_10"),
                                            p_20=Avg("recommendation__evaluationmetric__p_at_20"),
                                            p_30=Avg("recommendation__evaluationmetric__p_at_30"),
                                            p_40=Avg("recommendation__evaluationmetric__p_at_40"),
                                            p_50=Avg("recommendation__evaluationmetric__p_at_50"))
        precision = {}
        for i in p:
            key= i.name
            value= [i.p_10,i.p_20,i.p_30,i.p_40,i.p_50]
            precision[key]=value

        return precision
    elif metric_name=="mrr":
        p= model.Algorithm.objects.annotate(mrr_10= Avg("recommendation__evaluationmetric__mrr_at_10"),
                                            mrr_20=Avg("recommendation__evaluationmetric__mrr_at_20"),
                                            mrr_30=Avg("recommendation__evaluationmetric__mrr_at_30"),
                                           )
        mrr = {}
        for i in p:
            key= i.name
            value= [i.mrr_10,i.mrr_20,i.mrr_30]
            mrr[key]=value

        return mrr
    elif metric_name=="ndcg":
        p= model.Algorithm.objects.annotate(ndcg_10= Avg("recommendation__evaluationmetric__ndcg_at_10"),
                                            ndcg_20=Avg("recommendation__evaluationmetric__ndcg_at_20"),
                                            ndcg_30=Avg("recommendation__evaluationmetric__ndcg_at_30"),
                                            )
        ndcg = {}
        for i in p:
            key= i.name
            value= [i.ndcg_10,i.ndcg_20,i.ndcg_30]
            ndcg[key]=value

        return ndcg
    elif metric_name=="ctr":
        p= model.Algorithm.objects.annotate(ctr= Avg("recommendation__evaluationmetric__ctr"))
        ctr = {}
        for i in p:
            key= i.name
            value= i.ctr
            ctr[key]=value

        return ctr


def update_rating_matrix(user, paper, rating):
    """
        Saves the RatingMatrix Table when user updates his catalog through search.
        The function ensures only the latest rating is available for a user-paper combo
        :param rating: the actual rating value
        :param paper:
        :type paper: model.Paper
        :param user:
        :type user: model.User
        :return:
        :rtype: int
    """
    # check if its a rating addition for a particular algorithm
    rating=int(rating)
    # check if a rating exists for that paper
    user_mapping = user.usermapping_set.all()[0] # getting only the first object since its a one to one mapping


    rm_obj = model.RatingMatrix.objects.filter(user_map=user_mapping, paper=paper)
    # if rating exists then update that rating with new one
    if rm_obj.exists():
        rm_obj[0].rating = rating
        return rm_obj[0].save()
    # else create a new entry
    else:
        return model.RatingMatrix.objects.create(user_map=user_mapping,
                                                 paper=paper,
                                                 doc_id = paper.doc_id,
                                                 external_user_id = user_mapping.external_user_id,
                                                 rating=rating)


def convert_feedback_rating():
    """
       tranfer the ratings in UserFeedback to Rating Matrix table
        :return: int
    """
    # Get all ratings from Userfeedback and insert or update them in RAtingMATRIX
    feedback_items=model.UserFeedback\
                        .objects.values_list('recommendationresult_detail__recommendation__user',
                                             'recommendationresult_detail__paper',
                                             'user_rating',
                                             'datetime')
    for i in feedback_items:
        user_map=model.UserMapping.objects.get(user_id=i[0])
        obj,created=model.RatingMatrix.objects.get_or_create(user_map=user_map,
                                                 paper_id=i[1],
                                                 defaults={'rating': i[2]})
        obj.rating=i[2]
        obj.timestamp=i[3]
        obj.save()
    # todo extracting delta will improve execution
    return 1


def get_ratings(user_map=None):
    """
    Return the rating matrix for a particular algorithm or a vector
    :param User (user model object)
    :return: QuerySet
    """
    if user_map is None:
        return model.RatingMatrix.objects.all()
    else:
        return [i.paper.doc_id for i in model.RatingMatrix.objects.filter(external_user_id=user_map,rating=1)]

# end of code

def get_all_papers():
    return model.Paper.objects.all()


def does_paper_exist(url):
    return model.Paper.objects.filter(url=url).exists()

def get_paper_with_title(title):
    return model.Paper.objects.get(title=title)

def get_field_from_paper(field):
    return model.Paper.objects.values_list(field, flat=True)

def get_title_like(title_string):
    return model.Paper.objects.filter(title__icontains=title_string).values_list('title', flat=True)

def get_max_doc_id_from_papers():
    max_doc_id = model.Paper.objects.all().aggregate(Max('doc_id'))['doc_id__max']
    return max_doc_id


def get_model_paper_object(paper_dict):
    """
    Saves a paper meta data object in to the database
    :param paper:
    :type paper: PaperMetaData
    :return:
    :rtype: DB_MODEL
    """
    paper_model = model.Paper(url=paper_dict['paper_url'], title=paper_dict['title'],
                              abstract=paper_dict['abstract'], journal_name=paper_dict['journal_name'],
                              published_date=paper_dict['published_date'])
    print('Before validating unique')
    if paper_model.validate_unique():
        return paper_model

def get_user_catalog(user_id):
    return model.MyCatalog.objects.filter(user=user_id)


def get_model_author_object(author_name):
    return model.PaperAuthor(author_name=author_name)

def get_all_authors():
    return model.PaperAuthor.objects.all()


# catalog methods
def add_paper_to_catalog(paper, user_id):
    """
    Adds the paper to the catalog of user id
    :param paper: paper to be added
    :type paper: Paper
    :param user_id:
    :type user_id:
    :return:
    :rtype:
    """
    user = model.User.objects.get(id=user_id)
    if not user.mycatalog_set.exists():
        # user does not exist in catalog
        user_catalog = model.MyCatalog(user=user)
        user_catalog.save()
        user_catalog.papers.add(paper)
        user_catalog.save()
    else:
        # user exist in catalog
        user_catalog = model.MyCatalog.objects.get(user=user_id)
        user_catalog.papers.add(paper)
        user_catalog.save()
    '''Rating matrix related code beginning'''
    update_rating_matrix(user, paper, 1)

    '''Rating matrix related code end'''

def add_user(user_data):
    """
    Adds a user in to the database with its data as form
    :param user_data: form data
    :type user_data: Form
    :return:
    :rtype:
    """
    user = model.User(last_name=user_data.cleaned_data['last_name'], first_name=user_data.cleaned_data['first_name'],
                email=user_data.cleaned_data['email'], username=user_data.cleaned_data['username'],
                is_active=1,
                is_superuser=user_data.cleaned_data['is_superuser'], date_joined=timezone.now())
    user.set_password(user_data.cleaned_data['password'])
    user.save()
    return user

def add_user_mapping(user):
    # get max external id in the database
    max_user_id = model.UserMapping.objects.all().aggregate(Max('external_user_id'))['external_user_id__max']

    # increment the id by 1
    if max_user_id is None:
        external_user_id = 0
    else:
        external_user_id = max_user_id + 1

    # save the mapping object
    user_mapping = model.UserMapping(user=user, external_user_id=external_user_id)
    user_mapping.save()

