# Django Datatables Server-Side

> NOTE: this repository is archived. I haven't used this package for many years, it's not compatible with modern Django versions, and in a world of REST APIs, I'm not sure it's still meaningful.
> However, if you want to use it, feel free to fork!

This package provides an easy way to process Datatables queries in the server-side mode.

All you have to do is to create a new view, configure which model has to be used and which columns have to be displayed, and you're all set!

Supported features are pagination, column ordering and global search (not restricted to a specific column). The searching function can find values in any string-convertible field, and also searched with choice descriptions of predefined choices fields.

Foreign key fields can be used, provided that a QuerySet-like access path (i.e. model1__model2__field) is given in the configuration.

## How to use these views


Just create a new view that inherits **DatatablesServerSideView**. Here is a short example of a view that gives access to a simplistic model named *Employees*:

```python
class PeopleDatatableView(DatatablesServerSideView):
	# We'll use this model as a data source.
	model = Employees

	# Columns used in the DataTables
	columns = ['name', 'age', 'manager', 'department']

	# Columns in which searching is allowed
	searchable_columns = ['name', 'manager', 'department']

	# Replacement values for foreign key fields.
	# Here, the "manager" field points toward another employee.
	foreign_fields = {'manager': 'manager__name'}

	# By default, the entire collection of objects is accessible from this view.
	# You can change this behaviour by overloading the get_initial_queryset method:
	def get_initial_queryset(self):
		qs = super(PeopleDatatableView, self).get_initial_queryset()
		return qs.filter(manager__isnull=False)

	# You can also add data within each row using this method:
	def customize_row(self, row, obj):
		# 'row' is a dictionnary representing the current row, and 'obj' is the current object.
		row['age_is_even'] = obj.age%2==0
```

And this is a simple example of a template which will use our view (named "data-view" in the router):

```html
<!DOCTYPE html>
<html>
	<head>
		<meta charset="utf-8">
		<link rel="stylesheet" href="//cdn.datatables.net/1.10.19/css/jquery.dataTables.min.css">
	</head>
	<body>
		<h1>List of employees</h1>
		<hr>
		<table id="demo-table">
			<thead>
				<tr>
					<th>Name</th>
					<th>Age</th>
					<th>Department</th>
					<th>Manager</th>
				</tr>
			</thead>
			<tbody></tbody>
		</table>

		<script src="//code.jquery.com/jquery-3.3.1.min.js"></script>
		<script src="//cdn.datatables.net/1.10.19/js/jquery.dataTables.min.js"></script>
		<script language="javascript">
			$(document).ready(function () {
				/* Here begins the DataTable configuration. */
				$('#demo-table').DataTable({
					/* Tell the DataTable that we need server-side processing. */
					serverSide: true,
					/* Set up the data source */
					ajax: {
						url: "{% url "data-view" %}"
					},
					/* And set up the columns. Note that they must be identified by a "name" attribute,
					   with the value matching the columns in your Django view. The "data" attribute selects which record value will be used,
					   and should be the same value than for the "name" attribute. */
					columns: [
						{name: "name", data: "name"},
						{name: "age", data: "age"},
						{name: "department", data: "department"},
						{name: "manager", data: "manager"},
					]
				});
			});
		</script>
	</body>
</html>
```

The views will return HTTPResponseBadRequests if the request is not an AJAX request, or if parameters seems to be malformed.
