import django_tables2 as tables
from django.utils.html import mark_safe
from django.core.urlresolvers import reverse
from django_tables2.utils import A
from GUIManager.models import Algorithm


class UsersTable(tables.Table):
    class Meta:
        attrs = {'class': 'pltest'}
    id = tables.Column()
    username = tables.Column()
    email = tables.Column()
    last_name = tables.Column()
    first_name = tables.Column()
    last_login = tables.Column()
    is_superuser = tables.BooleanColumn()
    is_active = tables.BooleanColumn()
    date_joined = tables.Column()



class AlgorithmsTable(tables.Table):
    modify = tables.Column(empty_values=(), orderable=False)

    def render_modify(self, record):
        return mark_safe('<a class="btn btn-primary btn-sm" href=' + reverse("update_algorithm", args=[record.pk]) + '>Update</a>&nbsp'
                         '<a class="btn btn-primary btn-sm" href=' + reverse("delete_algorithm", args=[record.pk]) + '>delete</a>')

    class Meta:
        model = Algorithm
        attrs = {'class': 'table'}
        fields = ('id', 'name', 'created_by', 'description')
        order_by = 'id'
