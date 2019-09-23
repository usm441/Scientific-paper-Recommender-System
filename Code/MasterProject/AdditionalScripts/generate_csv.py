from django.db import connection
from AdditionalScripts import generate_paper_files as gen_paper, generate_user_files as gen_user
import os
from . import lda_csv

in_path = 'AdditionalScripts/input_files/'
out_path = 'AdditionalScripts/output_files/'

def generate_files():
    if not os.path.exists(out_path):
        os.makedirs(out_path)


    print('Generating metadata file')
    gen_paper.generate_db_metadata_file(metadata_file_path=in_path +'papers_metadata.csv', title_file=in_path+'full_metadata.csv',
                                        id_file=in_path+'citeulike_id_doc_id_map.csv', out_path=out_path)

    print('Generating vocab file')
    gen_paper.generate_vocab_file(terms_file=in_path+'terms.csv', out_path=out_path)


    print('Generating mapping file')
    gen_user.generate_user_mapping_file(users_file_path=in_path+'userhash_user_id_map.csv', out_path=out_path)

    print('Generating ratings file')
    gen_user.generate_ratings_file(ratings_file=in_path+'ratings.csv', outpath=out_path)
    #
    print('Generating LDA theta')
    lda_csv.create_ldatopics_sql(theta_file=in_path+'theta_150.dat', out_path=out_path)


def upload_files_in_db(truncate_tables):

    if truncate_tables:
        truncate_all_data()

    with connection.cursor() as cursor:

        # upload metadata file
        file_path = "/media/hamizahmed/085A870E5A86F7A8/Study\ Material/Semester\ 3/MS\ Project/SciPRecommender/Code/MasterProject" \
                    "/AdditionalScripts/output_files/"

        # metadata_upload_query = "SET autocommit=0;SET unique_checks=0;SET foreign_key_checks=0;" \
        #                         "LOAD DATA LOCAL INFILE '" + file_path + "'paper_meta_data_db.csv' + ' INTO TABLE " \
        #                         "sciprec_db.GUIManager_paper FIELDS TERMINATED BY '~' enclosed by '|' " \
        #                         "LINES TERMINATED BY '\\n' IGNORE 1 LINES; SET autocommit=1; SET unique_checks=1;foreign_key_checks=1;"
        # affected_count = cursor.execute(metadata_upload_query)
        # connection.commit()
        # print(str(affected_count) + ' rows inserted for paper')

        # # upload vocabulary file
        vocab_upload_query = "SET autocommit=0;SET unique_checks=0;SET foreign_key_checks=0; " \
                                "LOAD DATA LOCAL INFILE" + file_path + "'terms_db.csv' INTO TABLE " \
                                "GUIManager_vocabulary FIELDS TERMINATED BY ';' optionally enclosed by '|' LINES TERMINATED BY '\\n' IGNORE 1 LINES; SET autocommit=1; SET unique_checks=1;foreign_key_checks=1;"
        affected_count = cursor.execute(vocab_upload_query)
        connection.commit()
        print(str(affected_count) + ' rows inserted for vocab')

def truncate_all_data():
    with connection.cursor() as cursor:
        query_truncate_tables = "SELECT CONCAT('truncate table ',TABLE_SCHEMA, '.', table_name,';')" \
                                " FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'sciprec_db' AND TABLE_TYPE = 'BASE TABLE';"
        cursor.execute(query_truncate_tables)
        rows = cursor.fetchall()
        truncate_query = "SET foreign_key_checks=0;"
        for row in rows:
            truncate_query += row[0]
        truncate_query += 'SET foreign_key_checks=1;'

        cursor.execute(truncate_query)


if __name__ == "__main__":
    generate_files()