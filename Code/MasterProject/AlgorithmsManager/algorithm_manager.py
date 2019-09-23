from types import ModuleType
import EvaluationManager.Evaluation_Helpers as h
import shutil
import importlib
import sys
import os
from GUIManager.models import Algorithm,Paper,UserMapping
from django.db.utils import IntegrityError
import os



class AlgorithmNotFoundException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class ImportManager:
    """
    Class for managing algorithms (import, save etc) in project
    """

    def __init__(self):
        # Algorithm object
        self.algorithm = None
        # imported module object
        self.module = None
        self.algo_dir = os.path.join("AlgorithmsManager", "algorithms")

    def get_list_of_all_algorithms_in_app(self):
        """
        :return: a list containing names of all algorithms in the project
        """
        return [dir for dir in os.listdir(self.algo_dir)
                if os.path.isdir(os.path.join(self.algo_dir, dir)) and dir != '__pycache__']

    def load(self, algorithm_name):
        """
        call this method to load an algorithm. It imports the module containing the Script class and assigns the Script
        object to self.algorithm
        :param algorithm_name: Name of Algorithm to be loaded
        """
        dirs = self.get_list_of_all_algorithms_in_app()
        # Check if algorithm exists in the project
        if algorithm_name in dirs:
            # make ialgorithms.py and utils accessible to algorithm
            sys.path.append(os.path.join(sys.path[0], "AlgorithmsManager"))
            sys.path.append(os.path.join(sys.path[0], "AlgorithmsManager","utils"))

            algo_path = os.path.join(self.algo_dir, algorithm_name, algorithm_name)
            algo_path = algo_path.replace(os.path.sep, ".")

            self.module = self.import_module(algo_path)
            self.algorithm = self.module.Script()
            return self.algorithm
        else:
            raise AlgorithmNotFoundException("Can not find Algorithm with name : {}".format(algorithm_name))

    def upload(self, path_to_file, stats_file):
        """
        Add a new algorithm to project
        :param path_to_file: path to the algorithm file
        """
        # get the file name and extension of algorithm file
        filename, extension = os.path.splitext(os.path.basename(path_to_file))

        # create directory in project for new algorithm
        new_algo_location = os.path.join(self.algo_dir, filename)
        if not os.path.exists(new_algo_location):
            os.makedirs(new_algo_location)

        # copy algorithm to directory created above
        shutil.copy(path_to_file, new_algo_location)
        shutil.copy(stats_file, new_algo_location)

    def import_module(self, path):
        """
        imports a module
        :param path: path to python module
        :return: module object
        """
        return importlib.import_module(path)

    def import_code(self, code, name, doc_string="", add_to_sys_modules=False):
        """
        Imports Python modules
        :param code: a string, a file handle or an actual compiled code object
        :param name: the name given to module
        :param add_to_sys_modules: add to sys.modules if set
        :return: newly generated module
        """

        mod = ModuleType(name, doc_string)
        exec(code, mod.__dict__)
        if add_to_sys_modules:
            sys.modules['name'] = mod
        return mod

    def get_file_string(self, script_file):
        """
        get (script) file as a string
        :param script_file: path to file
        :return: string containing content of file
        """
        with open(script_file) as sf:
            script = sf.read()
        return str(script)

    def del_even_readonly(action, name, exc):
        import stat
        os.chmod(name, stat.S_IWRITE)
        os.remove(name)

    def delete_algorithm(self, algorithm_name):
        dirs = self.get_list_of_all_algorithms_in_app()
        # Check if algorithm exists in the project
        if algorithm_name in dirs:
            shutil.rmtree("{}/{}".format(self.algo_dir, algorithm_name), onerror=self.del_even_readonly)

    def rename_algorithm(self, algorithm_name, new_name):
        dirs = self.get_list_of_all_algorithms_in_app()
        # Check if algorithm exists in the project
        if algorithm_name in dirs:
            os.rename("{}/{}".format(self.algo_dir, algorithm_name), "{}/{}".format(self.algo_dir, new_name))


class AlgorithmManager:
    """
    Wrapper over ImportManager
    """

    def __init__(self):
        self.name = None
        self.ext = None
        self.created_by = None
        self.description = None
        self.id = None


    def delete_algorithm(self, algorithm_name):
        """
        delete a certain algorithm
        :param algorithm_name: name of algorithm
        """
        ImportManager().delete_algorithm(algorithm_name)

    def rename_algorithm(self, algorithm_name, new_name):
        """
        delete a certain algorithm
        :param algorithm_name: name of algorithm
        """
        ImportManager().rename_algorithm(algorithm_name, new_name)

    def insert_algorithm(self, name, created_by, description, file, replace_existing):
        """
        Insert algorithm in project and create a database entrz for it
        :param created_by: user object of the person who wrote this algorithm
        :param description: description of algorithm
        :param file: file handle for uploaded file
        :param replace_existing: flag (replace existing algorithm with the same name if True)
        :return: None if successful. otherwise string explaining the error
        """
        self.name = name
        self.ext = os.path.splitext(file.name)[1]
        self.created_by = created_by
        self.description = description

        try:
            dest_path = '/tmp/{}{}'.format(self.name, self.ext)
            stats_file = '/tmp/stats.txt'
            with open(dest_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            with open(stats_file, "w") as statsfile:
                statsfile.write(self.created_by.username + "\n" + self.description)
            algo_manager = ImportManager()
            algo_manager.upload(dest_path, stats_file)
            os.remove(dest_path)
            return None
        except IntegrityError:
            print("Algorithm with the same name already exists")
            return "Algorithm with the same name already exists"

    def get_recommendations(self, user_id, algorithm_id):
        try:
            recommendation_results=[]
            algorithm_name = Algorithm.objects.get(pk=algorithm_id).name
            im = ImportManager()
            im.load(algorithm_name)
            results=im.algorithm.get_recommendations(UserMapping.objects.get(user_id=user_id).external_user_id)
            doc_ids = [result[0] for result in results]
            paper_objs = Paper.objects.filter(doc_id__in=doc_ids)
            paper_dict = dict()
            for paper in paper_objs:
                paper_dict[paper.doc_id] = paper
            for index,result in enumerate(results):
                recommendation_results.append([index+1,
                                               paper_dict[result[0]],
                                               result[1]])
            return recommendation_results
        except:
            return h.get_recommendations(user_id, algorithm_id)

    def get_available_algorithms(self):
        """
        returns a list containing algorithm ids af all usable algorithms
        :return: list of algorithm ids
        """
        algo_ids = []
        algo_list = ImportManager().get_list_of_all_algorithms_in_app()
        db_algo_list = Algorithm.objects.filter(in_use=True)
        for algo in db_algo_list:
            if algo.name in algo_list:
                algo_ids.append(algo)
        return algo_ids


    def sync_database(self, user):
        """
        Synchronize database with existing algorithms in project. This adds missing entries to database and deletes
        extra entries. the descriptions have to be added later and the user provided as parameter(currently logged in
        user) becomes the owner of the algorithm.
        :param user: user who will become the owner of the algorithms
        """
        database_algo_set = {algorithm.name for algorithm in Algorithm.objects.all()}
        app_algo_set = set(ImportManager().get_list_of_all_algorithms_in_app())
        missing_entries_in_database = app_algo_set - database_algo_set
        extra_entries_in_database = database_algo_set - app_algo_set
        for entry in extra_entries_in_database:
            self.delete_algorithm_from_model(entry)
        for entry in missing_entries_in_database:
            algorithm = Algorithm(name=entry, created_by=user, description="")
            algorithm.save()





