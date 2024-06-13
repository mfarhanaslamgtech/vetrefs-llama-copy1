from flask import Flask
from flask_restful import Api
from chatbot.resources import (
    ChatbotResource,
    ChatHistoryResource,
    ChatListResource,
    DeleteChatSessionResource,
    DeleteAllChatsResource,
    ChatTitleRenameResource
)
from chatbot.chatbot import Chatbot
from flask import Flask, render_template
# from flask_restful import Api, Resource

# Initialize the Chatbot instance
chatbot = Chatbot()

# Flask app instance
app = Flask(__name__)
api = Api(app)  # Flask-RESTful instance

# Define route to render the HTML page
@app.route('/')
def welcome():
    return render_template('index.html')


# Add ChatbotResource as resources for the API endpoints with versioning
api.add_resource(ChatbotResource,
                    '/v1/chatbot', resource_class_args=(chatbot,),
                    endpoint='chatbot')

api.add_resource(ChatHistoryResource,
                    '/v1/chatbot/history/<int:user_id>/<int:chat_session_id>',
                    endpoint='history')

# Add the new resource class to the API
api.add_resource(ChatListResource,
                    '/v1/chatbot/chat_list/<int:user_id>',
                    endpoint='chat_list')

# Add resources for delete chat session
api.add_resource(DeleteChatSessionResource,
                    '/v1/chatbot/delete_chat_session/<int:user_id>/<int:chat_session_id>',
                    endpoint='delete_chat_session')

# Add resource for delete all chats
api.add_resource(DeleteAllChatsResource,
                    '/v1/chatbot/delete_all_chats/<int:user_id>',
                    endpoint='delete_all_chats')

# Add resource for rename the chat_title
api.add_resource(ChatTitleRenameResource,
                    '/v1/chatbot/rename_chat_title',
                    endpoint='rename_chat_title')


if __name__ == '__main__':
    # Start the Flask application with SSL enabled
    app.run(debug=True, host='0.0.0.0', port=5000)

