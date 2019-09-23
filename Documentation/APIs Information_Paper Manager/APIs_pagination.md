__IEEE:__

- API provides `max_records` parameter. Default value is 25 but can be increased up to 200.
- link: https://developer.ieee.org/docs/read/metadata_api_details/Sorting_and_Paging_Parameters.

__Springer:__

- API provides parameter `p` which is the numberof records to be returned. Maximum value is 100.
- link: https://dev.springernature.com/querystring-parameters

__PLOS:__

- API provides a `start` and `rows` parameter. E.g.for first page start=1 and rows=10 and for second page, start=10 and rows=10.
- Remember: Do not exceed 10 requests per minute.
- link: http://api.plos.org/solr/examples/

__arXiv:__

- API provides a `start` and `max_records` parameter for pagination.
- link: https://arxiv.org/help/api/user-manual#paging
