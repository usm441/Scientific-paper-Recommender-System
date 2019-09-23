from  Helpers import db_helper as db, paper_utilities as pap_utils
from PaperManager import paper_data_manager as pdm
import pdb

class UserManager():

    def __init__(self):
        pass

    def add_to_catalog(self, user_id, paper_title):
        paper = db.get_paper_with_title(paper_title)
        db.add_paper_to_catalog(paper, user_id)

    def does_paper_exist_in_user_catalog(self, user_id, paper):
        user_catalog = db.get_user_catalog(user_id)
        return user_catalog.filter(papers=paper).exists()

    def create_new_user(self, user_data):
        user = db.add_user(user_data)
        db.add_user_mapping(user)

    def get_catalog_papers(self, user):
        user_catalog = db.get_user_catalog(user.id)
        # pdb.set_trace()
        try:
            db_papers = user_catalog[0].papers.all()
        except:
            return []

        paper_manager = pdm.PaperDataManager()

        papers_dicts = []
        for db_paper in db_papers:
            serialized_paper = paper_manager.serialize_db_paper_into_dict(db_paper=db_paper, in_catalog=True)
            papers_dicts.append(serialized_paper)

        return papers_dicts

