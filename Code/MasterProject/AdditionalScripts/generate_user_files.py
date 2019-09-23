import pandas as pd
from django.contrib.auth.models import User
import GUIManager.models as model
from django.utils import timezone
from django.db.models import Max
import datetime
from pytz import timezone as tz
import csv

def generate_user_mapping_file(users_file_path, out_path):
    # read csv file as a dataframe
    users_df = pd.read_csv(users_file_path, sep=',', quotechar='|', quoting=csv.QUOTE_MINIMAL,
                           header=0,
                           dtype={'user_hash': str, 'user_id': int})
    # create a dummy user
    username = 'test'
    email = 'test@mailinator.com'
    password = '123'

    user = User(last_name='test', first_name='test',
                email=email, username=username,
                is_active=False,
                is_superuser=False, date_joined=timezone.now())
    user.set_password(password)
    user.save()
    user_id = user.pk



    # get max_external_user_id
    max_ext_user_id = model.UserMapping.objects.all().aggregate(Max('external_user_id'))['external_user_id__max']
    if not max_ext_user_id:
        max_ext_user_id = 0

    # create external user ids list
    # extract hash and user id from csv file
    ids = range(1, len(users_df)+1)
    hash = users_df['userhash'].values.tolist()
    external_user_ids = range(max_ext_user_id, len(users_df))
    user_ids = [user_id for i in range(len(users_df))]


    # save the df to csv
    final_df = pd.DataFrame({'id': ids, 'external_hash': hash, 'external_user_id': external_user_ids,
                             'user_id': user_ids})
    final_df.to_csv(out_path + 'usermap_db.csv',
                    columns=['id', 'external_hash', 'external_user_id', 'user_id'],
                    sep=';', line_terminator='\n', quotechar='|', quoting=csv.QUOTE_MINIMAL, index=False)


    print('Hello')


def generate_ratings_file(ratings_file, outpath):

    # load ratings file
    ratings_df = pd.read_csv(ratings_file, sep=',', names=['citeulike_id', 'user_hash', 'timestamp', 'tag'], index_col=False)

    # load user mapping file
    user_mapping_df = pd.read_csv(outpath+'usermap_db.csv', sep=';', quotechar='|', quoting=csv.QUOTE_MINIMAL,
                           dtype={'id': int, 'external_hash': str, 'external_user_id':int, 'user_id':int})

    # load paper data file
    papers_df = pd.read_csv(outpath+'paper_meta_data_db.csv', sep=';', quotechar='|', quoting=csv.QUOTE_ALL,
                            lineterminator='\n', index_col=False)

    # drop duplicates from it
    ratings_filtered_df = ratings_df[['citeulike_id', 'user_hash', 'timestamp']].drop_duplicates()

    # rename columns for merging of dataframes
    ratings_filtered_df.columns = ['external_hash', 'external_id', 'timestamp']

    # merge the two dataframes in external_hash
    map_ratings_df = user_mapping_df.merge(ratings_filtered_df, on='external_hash', how='inner', suffixes=['_map', '_rating'])

    map_ratings_df['external_id'] = map_ratings_df['external_id'].astype('int64')

    final_merged_df = map_ratings_df.merge(papers_df, on='external_id', how='inner', suffixes=['_mapping', '_paper'])

    # create relevant columns

    ids = range(1, len(final_merged_df)+1)
    rating = [1 for i in range(len(final_merged_df))]
    timestamp = final_merged_df['timestamp'].values.tolist()
    paper_id = final_merged_df['id_paper'].values.tolist()
    user_map_id = final_merged_df['id_mapping'].values.tolist()
    doc_ids = final_merged_df['doc_id'].values.tolist()
    external_user_ids = final_merged_df['external_user_id'].values.tolist()

    final_df = pd.DataFrame({'id': ids, 'rating': rating, 'timestamp':timestamp, 'paper_id': paper_id,
                             'user_map_id': user_map_id, 'doc_id':doc_ids,  'external_user_id':external_user_ids})

    final_df.to_csv(outpath+'ratings_db.csv',
                    columns=['id', 'rating', 'paper_id', 'timestamp', 'user_map_id', 'doc_id', 'external_user_id'],
                    sep=';', line_terminator='\n', quotechar='|', quoting=csv.QUOTE_MINIMAL, index=False)



