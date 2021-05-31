from flask import Flask
from flask_restplus import Api, Resource, reqparse, abort, fields, marshal_with
from werkzeug.contrib.fixers import ProxyFix
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='0.9.0', title='TodoMVC API',
    description='A simple TodoMVC API',
)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.sqlite3'

ns = api.namespace('todos', description='TODO operations')

todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details')
})

db = SQLAlchemy(app)
class tasks(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    due_by = db.Column(db.DateTime)
    status = db.Column(db.String(50))

    def __init__(self, due_by, status):
        self.due_by = due_by
        self.status = status

db.create_all()




class TodoDAO(object):
    def __init__(self):
        self.counter = 0
        self.todos = []

    def get(self, id):
        for todo in self.todos:
            if todo['id'] == id:
                return todo
        api.abort(404, "Todo {} doesn't exist".format(id))

    def create(self, data):
        todo = data
        todo['id'] = self.counter = self.counter + 1
        self.todos.append(todo)
        return todo

    def update(self, id, data):
        todo = self.get(id)
        todo.update(data)
        return todo

    def delete(self, id):
        todo = self.get(id)
        self.todos.remove(todo)


DAO = TodoDAO()
DAO.create({'task': 'Build an API'})
DAO.create({'task': '?????'})
DAO.create({'task': 'profit!'})


@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks'''
        return DAO.todos

    @ns.doc('create_todo')
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload), 201

@ns.route('/GET/<int:yyyy>/<int:mm>/<int:dd>')
@ns.response(404, 'Doesnot exists')
class Task(Resource):
    @ns.marshal_list_with(todo)
    def get(self,yyyy,mm,dd):
        d = datetime.datetime(yyyy,mm,dd)
        return tasks.query.filter_by(due_by=d).all()


@ns.route('/GET/finished')
@ns.response(404, 'Doesnot exists')
class Task(Resource):
    @ns.marshal_list_with(todo)
    def get(self):
        return tasks.query.filter_by(status='finished').all()


@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)
        return '', 204

    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, api.payload)


if __name__ == '__main__':
    app.run(debug=True)
