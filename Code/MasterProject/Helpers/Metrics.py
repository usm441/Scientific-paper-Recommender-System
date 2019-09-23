import GUIManager.models as model
import math


class Metrics:
    """
    Class to perform all evaluation metrics on the results
    returned from a recommendation query
    """

    def __init__(self, query):
        self.query = query
        self.recommendations = [result.paper_id
                                for result in
                                sorted(query.recommendationresult_set.reverse()
                                       , key = lambda result: result.predicted_rank)
                                ]

        def ground_truth_of_user(user_query):
            '''
            get ground truth based on my_catalog (and feedback table)
            :param user_query: Class Recommendation
            :return: List
            '''
            ground_truth_list = []

            # get all papers from user catalog
            # many to many relation on paper_id in mycatalog
            user_catalog=model.MyCatalog.objects.filter(user=user_query.user)
            if user_catalog.exists():
                user_catalog =user_catalog[0].papers.all()
            # Get all ratings entered by user till that page
            relevant_papers=model.UserFeedback.objects\
                .filter(recommendationresult_detail__recommendation__id=user_query.id,
                        user_rating=1,
                        feedback_type='explicit')
            ground_truth_list = ground_truth_list + [i.recommendationresult_detail.paper.id for i in relevant_papers]
            # TODO : COnsult if catalog has to be considerd as ground truth, if yes uncomment below line
            ''' ground_truth_list = ground_truth_list + [i.id for i in user_catalog] '''
            # remove any duplicates by converting to set
            return list(set(ground_truth_list))

        self.ground_truth = ground_truth_of_user(query)

    def precision_k(self, k):
        """
        :returns precision@k where k is the input parameter
        :rtype: int
        """

        # iterate thru actual hits and return True if found in recommendation
        c = [i in self.ground_truth for i in self.recommendations[:k]]
        return c.count(True) / k

    def mrr(self,k):
        """
        :returns mean reciprocal rank for the query result
        :rtype: int
        """
        for index, value in enumerate(self.recommendations[:k]):
            if value in self.ground_truth :
                return 1.0 / (index + 1)
        return 0


    def NDCG(self,pages):
        #TODO CORRECT THE CODE
        """
        :returns NDCG for the query result
        https://en.wikipedia.org/wiki/Discounted_cumulative_gain
        NDCG=DCG/maxpossible DCG
        DCG= Summation(rel1 + rel2/log(2) + rel3/log(3))
        where rel1 is 1 or 0 depending on if user found it relevant
        :rtype: int
        """
        def is_relevant(value):
            if value in self.ground_truth:
                return 1
            else:
                return 0
        # relevance of rank1
        dcg_sum = is_relevant(self.recommendations[0])
        '''code to calculate DCG'''
        # start enumerating from 2nd element with starting index as 2
        for index, value in enumerate(self.recommendations[1:pages], 2):
            dcg_sum = dcg_sum+is_relevant(value)/math.log2(index)

        # ideally maxdcg should be calculated till all the 10 or 20 r 30
        # recommendations but since relevance is 0 or 1 ,calculating till
        # len(ground_truth list) will also give the same result because non
        # relevant results contribute 0.0 to maxdcg

        max_dcg =1 + math.fsum(\
                 [1/math.log2(i+1) for i in range(1,len(self.ground_truth)-1)])
        return dcg_sum/max_dcg
