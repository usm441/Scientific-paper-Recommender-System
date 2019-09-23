
def get_serialized_dict(url, title, display_title, abstract, journal_name,
                        published_date, authors, source='', in_catalog=False):
    parsed_dict = dict(paper_url=url, display_title=display_title, title=title, abstract=abstract, journal_name=journal_name,
                       published_date=published_date, authors=authors, source=source, in_catalog=in_catalog)
    return parsed_dict


def get_authors_from_queryset(authors_query_set):
    if len(authors_query_set):
        authors_str = "By "
        for i, author in enumerate(authors_query_set):
            authors_str += author.author_name
            if not i == (len(authors_query_set) - 1):
                authors_str += ', '

        return authors_str
    return "Authors unknown"

def get_authors_from_list(authors_list):
    if len(authors_list):
        authors_str = "By "
        for i, author in enumerate(authors_list):
            authors_str += author
            if not i == (len(authors_list) - 1):
                authors_str += ', '

        return authors_str
    return "Authors unknown"