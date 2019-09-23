from django.shortcuts import render
from AlgorithmsManager.algorithm_manager import ImportManager
from AlgorithmsManager.algorithm_manager import AlgorithmManager
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from .model_forms import UserForm, AlgorithmsForm
from .models import Algorithm
from .tables import AlgorithmsTable
from django_tables2 import RequestConfig
from .model_forms import UserForm
import GUIManager.models as model
from django.http import JsonResponse
from PaperManager.paper_data_manager import PaperDataManager
import EvaluationManager.Evaluation_Helpers as h
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from UserManager.user_manager import UserManager
from django.contrib.auth import authenticate, login
import Helpers.db_helper as DBH
import json

def index(request):
    if request.user.is_authenticated:

        print(request.user.email)

        # Object containing all available algorithms in system
        #all_algorithms = model.Algorithm.objects.all()
        all_algorithms=AlgorithmManager().get_available_algorithms()
        catalog_count=len(DBH.get_user_catalog(request.user.id))

        if model.SystemRecommendations.objects.filter(isactive=True).exists():
            Systemalgo = model.SystemRecommendations.objects.get(isactive=True)
        else:
            Systemalgo = None
        response = render(request, 'GUIManager/home.html', {'algorithms': all_algorithms,
                                                            'Systemalgo': Systemalgo,
                                                            'catalog_count':catalog_count})
        # return render(request, 'GUIManager/home.html', {'first_name': request.user.first_name})
        return response
    else:
        # wrap.get_papers('Biology')
        return redirect('login')

def about(request):
    if request.user.is_authenticated:
        return render(request, 'GUIManager/about.html')
    else:
        return redirect('login')


def contact(request):
    if request.user.is_authenticated:
        return render(request, 'GUIManager/contact.html')
    else:
        return redirect('login')

def login_request(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                # Redirect to a success page.
                return redirect('home')
            else:
                # Return a 'disabled account' error message
                pass
        else:
            return render(request, 'GUIManager/login1.html', {
                'invalid_login': True
            })

    else:
        return render(request, 'GUIManager/login1.html', {
            'invalid_login': False
        })


def register(request):
    if request.method == 'POST':
        form = UserForm(request.POST)

        if form.is_valid():
            # user = User(last_name=form.cleaned_data['last_name'], first_name=form.cleaned_data['first_name'],
            #             email=form.cleaned_data['email'], username=form.cleaned_data['username'],
            #             is_active=form.cleaned_data['is_active'],
            #             is_superuser=form.cleaned_data['is_superuser'], date_joined=timezone.now())
            # user.set_password(form.cleaned_data['password'])
            # user.save()
            user_manager = UserManager()
            user_manager.create_new_user(form)
            return HttpResponseRedirect(reverse('home'))

    else:
        form = UserForm()
        return render(request, 'GUIManager/register.html', {'allow_superuser': False})


def add_user(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return render(request, 'GUIManager/register.html', {'allow_superuser': True})
        else:
            return HttpResponseRedirect(reverse('home'))
    else:
        return redirect('login')

def show_catalog(request):
    if request.user.is_authenticated:
        user_manager = UserManager()
        papers = user_manager.get_catalog_papers(request.user)
        return render(request, 'GUIManager/paper_list.html', {
            'paper_list': papers,
            'title': "Catalog Papers"
        })
    else:
        return redirect('login')

def show_ratedpapers(request):
    if request.user.is_authenticated:

        papers = h.get_rated_papers(request.user)
        paper_manager = PaperDataManager()

        return render(request, 'GUIManager/paper_list_rated.html', {
            'paper_list': papers,
            'title': "Papers marked relevant"
        })
    else:
        return redirect('login')

def search(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            search_query = request.GET.get('search_query')
            request.session['search_query'] = search_query
            paper_manager = PaperDataManager()
            papers_list = paper_manager.get_papers_for_query_from_db(user_id=request.user.id,
                                                                     search_query=search_query)
            return render(request, 'GUIManager/paper_list.html', {
                'paper_list': papers_list,
                'title': "Search Results from local database",
                'query': search_query
            })
    else:
        return redirect('login')


def external_search(request):
    search_query = request.session.get('search_query')
    paper_manager = PaperDataManager()
    papers_list = paper_manager.get_papers_from_external_sources(search_query)
    return render(request, 'GUIManager/paper_list.html', {
        'paper_list': papers_list,
        'title': "Search Results from external sources",
        'query': search_query
    })

def add_to_catalog(request):
    if request.user.is_authenticated:
        referer = request.META.get('HTTP_REFERER')
        if request.method == 'GET':
            title = request.GET.get('paper_title')
            user_manager = UserManager()
            user_manager.add_to_catalog(request.user.id, title)
            return JsonResponse({ 'sucessful':True  })
        else:
            return redirect('search')
    else:
        return redirect('login')


def add_algorithm(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            if request.method == 'POST':
                form = AlgorithmsForm(request.POST, request.FILES)

                if form.is_valid():
                    name = form.cleaned_data['name']
                    description = form.cleaned_data['description']
                    created_by = request.user
                    new_algorithm = Algorithm(name=name, description=description, created_by=created_by,
                                                  in_use=True)
                    new_algorithm.save()
                    algo_db_wrapper = AlgorithmManager()
                    algo_db_wrapper.insert_algorithm(name=name, description=description, created_by=created_by,
                                                     file=request.FILES['file'],
                                                     replace_existing=True)

                    return redirect('algorithms_table')
                else:
                    return redirect('algorithms_table')

            else:
                form = AlgorithmsForm()
                return render(request, 'GUIManager/add_model_object.html', {'form': form, 'header': 'Add Algorithm'})
        else:
            return render(request, 'GUIManager/unauth.html')
    else:
        return redirect('login')

def algorithms(request):
    if request.user.is_authenticated:
        table = AlgorithmsTable(Algorithm.objects.filter(in_use=True))
        RequestConfig(request).configure(table)
        return render(request, 'GUIManager/show_table.html',
                      {'table': table, 'name': 'Add algorithm', 'link': 'add_algorithm', 'show_button': True})
    else:
        return redirect('login')

def update_algorithm(request, algorithm_id):
    if request.user.is_authenticated:
        algorithm = Algorithm.objects.get(pk=algorithm_id)
        if request.user.username == algorithm.created_by.username:
            if request.user.is_superuser:
                if request.method == 'POST':
                    form = AlgorithmsForm(request.POST, request.FILES)

                    if form.is_valid():
                        algo_manager = AlgorithmManager()
                        name = form.cleaned_data['name']
                        description = form.cleaned_data['description']
                        created_by = request.user
                        new_name = "{}_{}".format(algorithm.name,timezone.localtime(timezone.now()))
                        algo_manager.rename_algorithm(algorithm.name, new_name)
                        algorithm.name = new_name
                        algorithm.in_use = False
                        algorithm.save()
                        updated_algorithm = Algorithm(name=name, description=description, created_by=created_by,
                                                      in_use=True, is_update_of=algorithm)
                        updated_algorithm.save()
                        algo_manager.insert_algorithm(name=name, description=description , created_by=created_by,
                                                         file=request.FILES['file'],
                                                         replace_existing=True)
                        return redirect('algorithms_table')
                    else:
                        return redirect('algorithms_table')

                else:
                    form = AlgorithmsForm(instance=algorithm)
                    return render(request, 'GUIManager/add_model_object.html',
                                  {'form': form, 'header': 'Add Algorithm'})
        else:
            return redirect('algorithms_table')
    else:
        return redirect('login')


def delete_algorithm(request, algorithm_id):
    if request.user.is_authenticated:
        algorithm = Algorithm.objects.get(pk=algorithm_id)
        if request.user.username == algorithm.created_by.username:
            AlgorithmManager().delete_algorithm(algorithm.name)
            algorithm.name = "{}_{}".format(algorithm.name,timezone.localtime(timezone.now()))
            algorithm.in_use = False
            algorithm.save()
            return redirect('algorithms_table')

        else:
            return redirect('algorithms_table')
    else:
        return redirect('login')


def getrecommendation(request):
    """
    Gets recommendations from the specified algorithm (step 0)
    and does these things:
    1. adds a query entry into Recommendation Table
    2. And inserts recommendations corresponding to previous query into RecommendationResult
    3. Process the result before sending to user
    :param request:
    :return:
    """
    if request.user.is_authenticated:
        if request.method == "POST":
            algoid = request.POST.get('algorithm')
            print(algoid, request.user.id)
            algo = model.Algorithm.objects.get(pk=algoid)
            usr = request.user
            # step 0: get recommendations from the requested algorithm
            # recommendations = h.get_recommendations(userid=usr.id,algoid=algo.id)
            recommendations = AlgorithmManager().get_recommendations(user_id=usr.id,
                                                                    algorithm_id=algo.id)
            # try:
            # step 1: insert an entry into Recommendation table
            reclog = model.Recommendation(algorithm=algo, user=usr,
                                          input_rating_count=h.get_rating_matrix_size())
            reclog.save()

            # step 2: insert the algorithm results corresponding to previous reclog id
            is_system_rec= request.POST.get('systemreco',None)
            h.add_recommendation(reclog, recommendations,is_system_rec)

            # step 3: Process the result before sending to user
            formatted_result_dict = h.process_user_recommendations(reclog)
            # except:
            #     return redirect('home')

            # pagination related code
            # initial page result is sent as 1
            page = 1
            # divide results into 10 entry per page
            paginator = Paginator(formatted_result_dict, 10)
            # update CTR
            h.update_ctr(reclog.id, page, for_pagination=True)
            try:
                recom = paginator.page(page)
            except PageNotAnInteger:
                recom = paginator.page(1)
            except EmptyPage:
                recom = paginator.page(paginator.num_pages)
            response = render(request,
                              'GUIManager/displayrecommendation.html',
                              {'recommendations': recom,
                               'algo': 'ScipR System' if is_system_rec is not None else algo.name,
                               'recommendation': reclog.id,
                               # to display alert message in result page
                               'message':'1'
                               }
                              )
            return response
        elif request.method == "GET":
            # Pagination related
            # get the recommendation list again
            try:
                recommendation = model.Recommendation.objects.get(id=request.GET.get('rec_id'))
            except:
                return redirect('home')
            if model.SystemAlgorithmRecommendationLog.objects.filter(recommendation=recommendation).exists():
                algo = 'ScipR System'
            else:
                algo=recommendation.algorithm.name
            page = request.GET.get('page', 1)
            # update CTR when a new page is shown
            h.update_ctr(request.GET.get('rec_id'), page, for_pagination=True)
            # divide results into 10 entry per page
            paginator = Paginator(h.process_user_recommendations(recommendation), 10)

            try:
                recom = paginator.page(page)
                # to prevent unauthorised attempts to view previous recommendations based on rec_id
                if request.user.id!=recommendation.user_id:
                    return redirect('home')
            except PageNotAnInteger:
                recom = paginator.page(1)
            except EmptyPage:
                recom = paginator.page(paginator.num_pages)
            response = render(request,
                              'GUIManager/displayrecommendation.html',
                              {'recommendations': recom,
                               'algo': algo,
                               'recommendation': request.GET.get('rec_id')
                               }
                              )
            return response
            # return HttpResponseRedirect(reverse('display_recommendation'))

    else:

        return redirect('login')


def process_feedback(request):
    if request.user.is_authenticated:
        try:

            recommendation_id = request.POST.get('recommendation_id')

            form_data=request.POST
            h.add_feedback(form_data, request.user.id)

            # getting newly filled user data
            recommendation=model.Recommendation.objects.get(id=recommendation_id)
            #check if it is system recommendation
            if model.SystemAlgorithmRecommendationLog.objects.filter(recommendation=recommendation).exists():
                algo = 'ScipR System'
            else:
                algo=recommendation.algorithm.name
            # pagination related
            page = request.POST.get('page', 1)
            # divide results into 10 entry per page
            paginator = Paginator(h.process_user_recommendations(recommendation), 10)
            recom = paginator.page(page)
            response = render(request,
                              'GUIManager/displayrecommendation.html',
                              {'recommendations': recom,
                               'algo': algo ,
                               'recommendation': recommendation_id,
                               'Success': "YOur feedback and changes were updated succesfully"
                               }
                              )
            return response

        except ValueError:

            response = render(request,
                              'GUIManager/displayrecommendation.html',
                              {'recommendations': recom,
                               'algo': recommendation.algorithm,
                               'recommendation': recommendation_id,
                               'Error': 'There was some problem'
                               }
                              )
            return response
    else:
        return redirect('login')


def eval_results(request):

    if request.GET.get('results')=='systemrecommendation':
        precision = DBH.get_metrics_systemrecommendations("precision")
        mrr = DBH.get_metrics_systemrecommendations("mrr")
        ndcg = DBH.get_metrics_systemrecommendations("ndcg")
        ctr = DBH.get_metrics_systemrecommendations("ctr")
    else:
        precision=DBH.get_metrics("precision")
        mrr = DBH.get_metrics("mrr")
        ndcg = DBH.get_metrics("ndcg")
        ctr = DBH.get_metrics("ctr")

    precision_label=[algo_name for algo_name in precision.keys()]
    p10_data = [0 if not precision[i][0] else precision[i][0] for i in precision_label]
    p20_data = [0 if not precision[i][1] else precision[i][1] for i in precision_label]
    p30_data = [0 if not precision[i][2] else precision[i][2] for i in precision_label]
    p40_data = [0 if not precision[i][3] else precision[i][3] for i in precision_label]
    p50_data = [0 if not precision[i][4] else precision[i][4] for i in precision_label]


    mrr_label = [algo_name for algo_name in mrr.keys()]
    mrr10_data = [0 if not mrr[i][0] else mrr[i][0] for i in mrr_label]
    mrr20_data = [0 if not mrr[i][1] else mrr[i][1] for i in mrr_label]
    mrr30_data = [0 if not mrr[i][2] else mrr[i][2] for i in mrr_label]


    ndcg_label = [algo_name for algo_name in ndcg.keys()]
    ndcg10_data = [0 if not ndcg[i][0] else ndcg[i][0] for i in ndcg_label]
    ndcg20_data = [0 if not ndcg[i][1] else ndcg[i][1] for i in ndcg_label]
    ndcg30_data = [0 if not ndcg[i][2] else ndcg[i][2] for i in ndcg_label]


    ctr_label = [algo_name for algo_name in ctr.keys()]
    ctr_data = [0 if not ctr[i] else ctr[i] for i in ctr_label]
    response = render(request,
                      'GUIManager/evaluationresults.html',
                      {'precision_labels':precision_label,
                       'p10_data': json.dumps(p10_data),
                       'p20_data': p20_data,
                       'p30_data': p30_data,
                       'p40_data': p40_data,
                       'p50_data': p50_data,
                       'mrr10_data':mrr10_data,
                       'mrr20_data': mrr20_data,
                       'mrr30_data': mrr30_data,
                       'ndcg10_data':ndcg10_data,
                       'ndcg20_data': ndcg20_data,
                       'ndcg30_data': ndcg30_data,
                       'ctr_data':ctr_data
                       })
    return response


def add_ctr(request):

    page = request.GET.get('page', 1)
    h.update_ctr(request.GET.get('rec_id'),page)

    return redirect(request.GET.get('exurl'))

def show_feedback_rating(request):
    if request.user.is_authenticated:
        ratings=DBH.get_feedback_ratings()
        response = render(request,
                          'GUIManager/evaluation_manager.html',
                          {'ratings': ratings,
                           'all_algorithms': AlgorithmManager().get_available_algorithms(),
                           'past_system_algo': model.SystemRecommendations.objects.all(),
                           'ratingmatrix': model.RatingMatrix.objects.count()}
                          )
        return response

    else:

        return redirect('login')


def convert_feedback_rating(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            DBH.convert_feedback_rating()
            ratings = DBH.get_feedback_ratings()
            response = render(request,
                              'GUIManager/evaluation_manager.html',
                              {'ratings': ratings,
                               'all_algorithms': AlgorithmManager().get_available_algorithms(),
                               'past_system_algo': model.SystemRecommendations.objects.all(),
                               'ratingmatrix': model.RatingMatrix.objects.count(),
                               'Success': "Rating Matrix updated succesfully"
                               }
                              )

            return response

    else:

        return redirect('login')

def update_system_recommendation(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            h.set_system_recommendation(request.user,request.POST.get('algo_id'),
                                        request.POST.get('comment'))
            ratings = DBH.get_feedback_ratings()
            all_algorithms = AlgorithmManager().get_available_algorithms()
            response = render(request,
                              'GUIManager/evaluation_manager.html',
                              {'ratings': ratings,
                                'all_algorithms':all_algorithms,
                               'past_system_algo': model.SystemRecommendations.objects.all(),
                               'Success': "Your changes were updated succesfully"
                               }
                              )

            return response

    else:

        return redirect('login')