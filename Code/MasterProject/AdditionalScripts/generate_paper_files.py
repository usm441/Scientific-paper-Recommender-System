import pandas as pd
from Helpers import utilities as utils
from django.db.models import Max
import GUIManager.models as model
import numpy as np
import datetime
import csv


def generate_db_metadata_file(metadata_file_path, title_file, id_file, out_path):

    # load papers dataframe
    papers_df = pd.read_csv(title_file, sep=',', quotechar='"', quoting=csv.QUOTE_MINIMAL,
                dtype={'citeulike_id': int, 'type': str, 'journal': str, 'booktitle': str,
                       'series': str, 'publisher': str, 'pages': str, 'volume': str,
                       'number': str, 'year': str, 'month': str, 'postedat': str, 'address': str,
                       'title': str, 'abstract': str})

    # load metadata dataframe
    metadata_df = pd.read_csv(metadata_file_path, sep=',', quotechar='"', quoting=csv.QUOTE_MINIMAL,
                              dtype={'citeulike_id': int, 'type': str, 'journal': str, 'booktitle': str,
                                     'series': str, 'publisher': str, 'pages': str, 'volume': str,
                                     'number': str, 'year': str, 'month': str, 'postedat': str, 'address': str,
                                     'text':str}
                              )

    doc_ids_df = pd.read_csv(id_file, sep=',', dtype={'citeulike_id':int, 'doc_id':int})

    # merge the two dataframes on citeulike id
    merged_df_title = metadata_df.merge(papers_df, on='citeulike_id', how='inner', suffixes=['_l', '_r'])

    final_merged = merged_df_title.merge(doc_ids_df, on='citeulike_id', how='inner', suffixes=['_l', '_r'])

    # extract dataframes in relevant lists
    ids = list(range(1, len(final_merged)+1))
    external_ids = final_merged['citeulike_id'].values.tolist()
    urls = ('http://www.citeulike.org/article/' + final_merged['citeulike_id'].astype(str)).values.tolist() # create urls metadata_df


    # filter sepcial characters
    final_merged['text'] = final_merged['text'].str.replace(';', ' ')
    final_merged['journal_l'] = final_merged['journal_l'].str.replace(';', ' ')
    final_merged['text'] = final_merged['text'].str.replace('\n', ' ')
    # remove numeric and special characters
    final_merged['title'] = final_merged['title'].str.replace('[^\s\w]', ' ')
    # remove more than one space
    final_merged['title'] = final_merged['title'].str.replace(' +', ' ')
    # remove spaces from front and back
    final_merged['title'] = final_merged['title'].str.lstrip()
    final_merged['title'] = final_merged['title'].str.rstrip()
    # merged_df_title['title'] = merged_df_title['title'].str.replace('{', '')
    # merged_df_title['title'] = merged_df_title['title'].str.replace('}', '')

    # treating special case, removing \ from its title
    # locs = np.where(merged_df_title.title.apply(lambda x: x == 'the progressive nature of wallerian degeneration '
    #                                                                  'in wild-type and slow wallerian degeneration (\\wlds) nerves'))
    # value = merged_df_title.iloc[locs[0][0], merged_df_title.columns.get_loc('title')].replace('\\', '')
    # merged_df_title.ix[locs[0][0], 'title'] = str(value)

    # replace nan with empty string
    final_merged['title'] = final_merged['title'].replace(np.nan, '', regex=True)
    final_merged['journal_l'] = final_merged['journal_l'].replace(np.nan, '', regex=True)

    # strip the string to 250 characters
    final_merged['title'] = final_merged['title'].str[:200]
    final_merged['journal_l'] = final_merged['journal_l'].str[:250]

    # fill empty title with its id
    empty_title_locs = np.where(final_merged.title.apply(lambda x: x == ''))

    for loc in empty_title_locs[0]:
        value = final_merged.iloc[loc, final_merged.columns.get_loc('citeulike_id')]
        final_merged.ix[loc, 'title'] = str(value)


    # appending ids to duplicate values

    final_merged['title'] = final_merged.groupby('title').title.apply(lambda n: n + final_merged.citeulike_id[final_merged['title'].isin(n)].astype(str) if len(n)>1 else n)

    # extract them to list
    journals = final_merged['journal_l'].values.tolist()
    abstracts = final_merged['text'].values.tolist()
    titles = final_merged['title'].values.tolist()

    doc_ids = final_merged['doc_id'].values.tolist()

    # get max_doc_id
    # max_doc_id = model.Paper.objects.all().aggregate(Max('doc_id'))['doc_id__max']
    # if not max_doc_id:
    #     max_doc_id = 0

    # extract dates and doc_ids
    dates = []
    # doc_ids = []
    for i, row in final_merged.iterrows():
        month = row['month_l']
        year = row['year_l']

        if utils.is_month_valid(month) and utils.is_valid_year(year):
            # if month and year are valid, create date out of them
            date = datetime.datetime(int(year), utils.get_month_num(month), 1, 0, 0)
            date = date.strftime('%Y-%m-%d')
        else:
            # create date from postedat
            datetime_obj = datetime.datetime.strptime(row['postedat_l'], "%Y-%m-%d %H:%M:%S")
            date = datetime_obj.strftime('%Y-%m-%d')
        dates.append(date)

        # if max_doc_id == 0:
        #     doc_id = int(max_doc_id) + int(i)
        # else:
        #     doc_id = int(max_doc_id) + int(i) + 1
        #
        # doc_ids.append(doc_id)

    # create final dataframe
    final_df = pd.DataFrame({'id':ids, 'url':urls, 'title':titles, 'abstract':abstracts,
                             'journal_name':journals, 'published_date':dates, 'doc_id':doc_ids, 'external_id':external_ids})
    final_df.to_csv(out_path+'paper_meta_data_db.csv', columns=['id', 'doc_id', 'url', 'external_id', 'published_date', 'journal_name',
                                                        'title', 'abstract'],
                    sep=';', line_terminator='\n', quotechar='|', quoting=csv.QUOTE_ALL, index=False)


def generate_vocab_file(terms_file, out_path):
    # read the terms file
    terms_df = pd.read_csv(terms_file, header=None, usecols=[0])

    # generate term ids
    ids = list(range(0, len(terms_df)))

    # extract list out of term ids
    terms_list = terms_df[0].values.tolist()

    final_df = pd.DataFrame({'term_id':ids, 'term':terms_list})
    final_df.to_csv(out_path+'terms_db.csv', columns=['term_id', 'term'],
                    sep=';', line_terminator='\n', quotechar='"', quoting=csv.QUOTE_MINIMAL, index=False)

# def test(n):


# def add_id_to_title(titles):
#     ids =

if __name__ == "__main__":
    generate_db_metadata_file('papers_metadata.csv')