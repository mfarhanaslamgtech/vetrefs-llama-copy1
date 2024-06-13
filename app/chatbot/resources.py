import inspect
from flask_restful import Resource
from werkzeug.exceptions import NotFound
from flask import request,jsonify
from logs.logger import configure_logging
from database.db_operations import DatabaseHandler

logging = configure_logging()
#create instance of DbOperations
db_handler = DatabaseHandler()

# Created ChatbotResource class 
class ChatbotResource(Resource):
    """
    Resource class for handling user interactions with the chatbot.

    This class defines an endpoint for processing user questions 
    and managing chat sessions. It utilizes the Chatbot class to 
    provide responses and store chat history in the database.

    Methods:
    - post: Handle HTTP POST requests to answer user questions 
    and manage chat sessions.

    Attributes:
    - chatbot (Chatbot): An instance of the Chatbot class for 
    managing chat interactions.

    Rate Limiting:
    Rate limiting is applied to control the number of requests per 
    minute and per day. Requests beyond the specified limits will 
    result in an HTTP 429 Too Many Requests response.

    Note: This class extends the Flask-RESTful Resource class.

    Usage Example:
    ```
    chatbot = Chatbot()
    api.add_resource(ChatbotResource, 
    '/v1/chatbot', resource_class_args=(chatbot,), endpoint='chatbot_resource')
    ```
    """

    def __init__(self, chatbot):
        """
        Constructor method to initialize the ChatbotResource.

        Parameters:
        - chatbot (Chatbot): An instance of the Chatbot class for managing chat interactions.
        """
        self.chatbot = chatbot
        self.db_handler = db_handler
    
    # Apply rate limiting for certin request per minute and request per day
    # @limiter.limit("2 per minute; 100 per day", error_message="Sorry, you have exceeded the rate limit. Please try again later.")

    # Defined the HTTP POST method to handle user questions in JSON format
    def post(self):
        """
        Handle HTTP POST requests to answer user questions
          and manage chat sessions.

        This method processes incoming JSON data, extracts 
        user_id, chat_session_id, and question,
        and delegates the question to the associated Chatbot
          instance. It also generates and saves
        chat titles and returns the response along with the
          chat_session_id.

        Returns:
        - dict: A dictionary containing the chatbot's answer
          and the associated chat_session_id.
          Example: {'answer': 'Response text.', 'chat_session_id': 1}
        """
        try:
            # get the data from incoming request
            data = request.get_json()

            # Extract user_id and chat_session_id from the request data
            user_id = data.get("user_id")
            chat_session_id = data.get("chat_session_id")
            question = data.get("question")
            # print(type(question)) 

            # If chat_session_id is not a valid numeric int, generate a new one
            if not isinstance(chat_session_id, int) :
                chat_session_id = self.db_handler.generate_chat_session_id(user_id)
                data["chat_session_id"] = chat_session_id  

            # Process the request using the provided or generated chat_session_id
            answer = self.chatbot.answer_question(user_id, chat_session_id, question)

            # Generate and save chat title
            generated_chat_title = self.db_handler.generate_chat_title(user_id, chat_session_id)
            
            # save the chat title
            self.db_handler.save_chat_title(user_id, chat_session_id, generated_chat_title)
            # return the response
            response =  {'answer': answer, 'chat_session_id': chat_session_id}
            return response
        
        except Exception as e:
            # Log the error
            # logging.error(f"An error occurred while processing a request: {str(e)}")
            logging.error(f"An error occurred while processing a request",exc_info=True)
            return {'error': 'An error occurred while processing your request.'}, 500

  
# Created ChatHistoryResource class to retrieve chat history
class ChatHistoryResource(Resource):
    """
    Resource class for retrieving chat history for a specific user 
    and chat session.

    Methods:
    - get(self, user_id, chat_session_id): Retrieve chat history for
      a specific user and chat session.

    """
    def __init__(self):
        self.db_handler = db_handler

    # Defined the HTTP GET to retrieve chat history
    def get(self, user_id, chat_session_id):
        """
        Retrieve and format chat history for a specific user 
        and chat session.

        Parameters:
        - user_id (int): The unique identifier for the user.
        - chat_session_id (int): The identifier for the chat_session.

        Returns:
        - dict: A formatted dictionary containing chat history.

        Raises:
        - NotFound: If the chat history is not found in the database.

        """
        try:
            chat_history = self.db_handler.get_chat_history(user_id, chat_session_id)
            return jsonify(chat_history)
        except Exception as e:
            logging.error(f"Chat history not found: {str(e)}")
            return {'error': 'Chat history not found!.'}, 404
        
        
class ChatListResource(Resource):
    """
    Resource for retrieving a list of chat sessions for a user.

    Methods:
    - get(user_id: int) -> dict:
        Retrieve a list of chat sessions with their corresponding
          first questions.

    - get_chat_title(user_id: int, chat_session_id: int) -> str:
        Retrieve the chat title for a specific chat session.

    """
    def __init__(self):
        #instance attribute
        self.db_handler = db_handler
        

    # Defined the HTTP GET method to retrieve all chat sessions for a user
    def get(self, user_id):
        """
        Retrieve a list of chat sessions with their corresponding
          first questions.

        Args:
        - user_id (int): The unique identifier for the user.

        Returns:
        - dict: A dictionary containing chat sessions along with 
        their first questions.
          Example:
          {
            "chat_sessions": [
              {"chat_session_id": 1, "chat_title": "First Chat"},
              {"chat_session_id": 2, "chat_title": "Second Chat"}
            ]
          }
        """

        try:
            # Query the database to get all chat sessions for the user
            chat_sessions = self.db_handler.get_chat_sessions(user_id)
            print(" chat sessions", chat_sessions)
            # Create a dictionary to store chat sessions with corresponding first questions
            chat_sessions_with_questions = []

            # Populate the chat_sessions_with_questions dictionary
            for chat_session_id in chat_sessions:
                chat_title = self.db_handler.get_chat_title(user_id, chat_session_id)
                
                # chat_sessions_with_questions[chat_session_id] = first_question
                chat_sessions_with_questions.append(
                    {"chat_session_id":chat_session_id, "chat_title":chat_title}
                    )
            # If the list is empty, raise an exception
            if not chat_sessions_with_questions:
                raise Exception()

            # Return the list of chat sessions with corresponding first questions in the response
            response = {'chat_sessions': chat_sessions_with_questions}
             
            return response
        except Exception as e:
            # Log the error
            logging.error(f"Chat list not found!: {str(e)}")
            return {'error': 'Chat list not found!!.'}, 404


# class for rename the chat_title
class ChatTitleRenameResource(Resource):
    """
    Resource for renaming the chat title of a specific chat session.

    Attributes:
    - chatList (ChatList): An instance of the ChatList class.

    Methods:
    - put() -> dict:
        Update or rename the chat title for a specific chat session.

    Description:
    This resource provides an API endpoint for updating or renaming 
    the chat title of a specific chat session. It is associated with
      the ChatList class, which is responsible for managing the list 
      of chat sessions.

    Methods:
    - put() -> dict:
        Update or rename the chat title for a specific chat session. 
        This method expects a JSON payload containing the user_id, 
        chat_session_id, and chat_title. It validates the input, checks
          the existence of the chat session, and updates the chat title 
          in the database.

    Example Usage:
    Suppose a user wants to rename the chat title for a chat session. 
    They can send a PUT request to the
    '/v1/chatbot/rename_chat_title' endpoint with a JSON payload 
    containing the user_id, chat_session_id, and
    the new chat_title. If successful, the method returns a success message.

    """
    def __init__(self):
        self.db_handler = db_handler
    
    # Apply rate limiting for certin request per minute and request per day
    # @limiter.limit("10 per minute; 100 per day")

    # define the put method to update/rename the chat_title
    def put(self):
            """
        Update or rename the chat title for a specific 
        chat session.

        Payload:
        {
        # The unique identifier for the user.
          "user_id": int,
           # The unique identifier for the chat session.  
          "chat_session_id": int,
          # The new chat title to be set for the chat session. 
          "chat_title": str          
        }

        Returns:
        - dict: A dictionary indicating the success or error
          message.
          Example:
          {"success": "Chat title updated successfully!"}

        Raises:
        - NotFound: If the specified chat session does not exist.
        - ValueError: If the chat title is empty, contains 
        whitespace, or exceeds the maximum length.
        - Exception: If an unexpected error occurs.
        """
            try:
                # get the data from incoming request
                data = request.get_json()
                user_id = data.get("user_id")
                chat_session_id = data.get("chat_session_id")
                chat_title = data.get("chat_title")
                
                # validate if chat title does't exist against the given parameters
                if not self.db_handler.does_chat_title_exist(user_id, chat_session_id, chat_title):
                    raise NotFound("Chat session does not exist!")
                
                max_chat_title_len = 50
                # validate if the chat_title is empty or contain whitspace and check length
                if not chat_title.strip():
                    raise ValueError("Chat title cannot be empty or whitespace.")
                # validate the length of chat_title in characters
                elif len(chat_title) > max_chat_title_len:
                    raise ValueError(f"Chat title length should not exceed {max_chat_title_len} characters.")
            
                # call the method to rename chat title
                self.db_handler.rename_chat_title(user_id, chat_session_id, chat_title)
                return {'success': 'Chat title updated successfully!'}
            
            # catch exception if the chat_title  does not exist
            except NotFound as nfe:
                # log the error
                logging.error(f"ValueError:{str(nfe)}")
                return {'error':str(nfe)}, 404 
            
            # Catch exception if the chat title is empty or contain whitespace 
            except ValueError as ve:
                # Log the error
                logging.error(f"ValueError: {str(ve)}")
                return {'error': str(ve)}, 400

            # Catch exception if any unexpected error occured 
            except Exception as e:
                # Log the error 
                logging.error(f"An unexpected error occured :{str(e)}")
                return {'error':'An unexpected error occured.'}, 500
    

# define class to delete the chat session
class DeleteChatSessionResource(Resource):
    """
    Resource for deleting a specific chat session.

    Methods:
    - delete(user_id: int, chat_session_id: int) -> dict:
        Delete a specific chat session.

    - check_data_existence(user_id: int, chat_session_id: int) -> bool:
        Check if the specified chat session exists in the database.

    - delete_chat_session(user_id: int, chat_session_id: int) -> None:
        Delete the specified chat session from the database.

    """
    def __init__(self):
        self.db_handler = db_handler
    
    # Apply rate limiting for certin request per minute and request per day
    # @limiter.limit("10 per minute; 100 per day")

    def delete(self, user_id, chat_session_id):
        """
        HTTP DELETE method to delete a specific chat session.

        Args:
        - user_id (int): The ID of the user associated with 
        the chat session.
        - chat_session_id (int): The ID of the chat session
          to be deleted.

        Returns:
        - dict: A dictionary indicating the status of the 
        deletion operation.

        Description:
        This method is called when an HTTP DELETE request is
          made to the
          '/v1/chatbot/delete_chat_session/<user_id>/
          <chat_session_id>' endpoint.
        It checks if the specified chat session exists in the
          database and deletes it if found.

        Example Usage:
        ```
        response = resource.delete(user_id=1, chat_session_id=123)
        ```

        """
        try:
            # Checkif the data exists in the database
            if not self.db_handler.check_session_existence(user_id, chat_session_id):
                raise NotFound("Chat does not exist!")

            # Your existing logic to delete the chat session
            self.db_handler.delete_chat_session(user_id, chat_session_id)

            # return the status message 
            return {'message': 'Deleted successfully'}
        
        # catch the NotFound exception
        except NotFound as nfe:
            # Log the error
            logging.error(f"NotFound: {str(nfe)}")
            return {'error':str(nfe)},404 
    

# define class to delete the data
class DeleteAllChatsResource(Resource):
    """
    Resource for deleting all chat sessions for a 
    specific user.

    Methods:
    - delete(user_id: int) -> dict:
        Delete all chat sessions for a specific user.

    - check_data_existence(user_id: int) -> bool:
        Check if any chat sessions exist for the 
        specified user.

    - delete_all_chats(user_id: int) -> None:
        Delete all chat sessions for the specified 
        user from the database.

    """
    def __init__(self):
        self.db_handler = db_handler

    # Apply rate limiting for certin request per minute and request per day
    # @limiter.limit("20 per minute; 100 per day")

    #define the delete method to delete the all chats
    def delete(self, user_id):
        """
        HTTP DELETE method to delete all chat sessions
          for a specific user.

        Args:
        - user_id (int): The ID of the user whose chat
          sessions will be deleted.

        Returns:
        - dict: A dictionary indicating the status of
          the deletion operation.

        Description:
        This method is called when an HTTP DELETE 
        request is made to the 
        '/v1/chatbot/delete_all_chats/<user_id>' 
        endpoint.
        It checks if any chat sessions exist for the
          specified user and deletes
          them if found.

        Example Usage:
        ```
        response = resource.delete(user_id=1)
        ```

        """
        try:
            if user_id is None:
                return {'message':'user id cannot be None'}, 404
            if not self.db_handler.check_user_existence(user_id):
                return {'message':'Data does not exist'}, 404
            
            self.db_handler.delete_all_chats(user_id)
            return {'message':'Deleted successfully!'}
        
        except Exception as e:
            logging.error(f"An error occured while processing your request :{str(e)}")
            return {'message':'An error occured while processing your request'}
   
   