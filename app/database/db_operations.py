# Importing from subdirectories
import json
import pymongo
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    messages_from_dict,
    messages_to_dict,
) 
import datetime
from database.db_connection import db_connector

class DatabaseHandler:
    def __init__(self):
        self.db = db_connector()

    # method to save the original(first) chat_history 
    def save_new_session_chat(self, user_id, chat_session_id, serialized_message):
        """
        Save the original chat history to database.

        Args: 
            user_id (int) : The id of the user.
            chat_session_id (int) : The ID  of the 
            chat session.
            serialized_message (str) : The serialized 
            messages containing chat_history
        """
        document = {
            "user_id":user_id,
            "chat_session_id":chat_session_id,
            "messages": serialized_message,
            "timestamp":datetime.datetime.now()
        }
        self.db.chat_history.insert_one(document)

    # method to save the reloaded_chat_history (for second block -- which you will see in answer_question method)
    def update_existing_session_chat(self, user_id, chat_session_id, serialized_message):
        """
        Updates and saves reloaded chat history to the 
        database.

        Args:
            user_id (int): The ID of the user.
            chat_session_id (int): The ID of the chat 
            session.
            serialized_message (str): The serialized 
            message containing chat history.
        """         
        #update conversation into mongodb
        document = {
            "user_id":user_id,
            "chat_session_id":chat_session_id,
            "messages":serialized_message,
            "timestamp":datetime.datetime.now()
        }
        # replace the document based on the user_id and chat_session_id 
        self.db.chat_history.replace_one({"user_id":user_id, "chat_session_id":chat_session_id}, document)
 
    #method for checking the data into database(this will retrieve the complete document based on user and chat_session id)
    def check_into_db(self, user_id, chat_session_id):
        """
        Checks if data exist against a specific user_id and 
        chat_session_id in the database.

        Args:
            user_id (int): The ID of the user.
            chat_session_id (int): The ID of the chat session.

        Returns:
            dict or None:
            The retrieved document (retrieved_from_db) from the
              database can be dict or None if not found.
        """
        query = {"user_id":user_id, "chat_session_id":chat_session_id}
        retrieved_from_db = self.db.chat_history.find_one(query)
        return retrieved_from_db

    # define the function to generate chat_session_id
    def generate_chat_session_id(self, user_id):
        """
        Generate a chat_session_id for a user based on 
        their previous chat history.

        Parameters:
        - user_id (int): The unique identifier for the user.

        Returns:
        - int: The generated or incremented chat_session_id.
        """
        # Get the most recent chat_session_id for the user from the database
        most_recent_session_id = self.db.chat_history.find_one(
            {'user_id': user_id},
            sort=[('timestamp', -1)]
        )
        # Increment the most recent chat_session_id or initialize to 1 if none exists
        if most_recent_session_id and isinstance(most_recent_session_id['chat_session_id'], int):
            current_chat_session_id = most_recent_session_id['chat_session_id'] + 1
        else:
            current_chat_session_id = 1
        return current_chat_session_id
    

    # Function to get the first human question from a chat session
    def generate_chat_title(self, user_id, chat_session_id):
        """
        Generate a chat title for a given user and chat session.

        Parameters:
        - user_id (int): The unique identifier for the user.
        - chat_session_id (int): The identifier for the chat session.

        Returns:
        - str: The generated chat title.
        """
        # Query to get the most recent collection against the chat_session_id with respect to timestamp
        most_recent_collection = self.db.chat_history.find_one(
            {"user_id": user_id, "chat_session_id": chat_session_id}
        )
        extracted_messages = messages_from_dict(json.loads(most_recent_collection["messages"]))
        generated_chat_title = extracted_messages[0].content[:50]  # limit to first 50 characters
        return generated_chat_title


    # Function to save the generated chat_title in document
    def save_chat_title(self, user_id, chat_session_id, generated_chat_title):
        """
        Save the generated chat title in the database for a given user
        and chat session.

        Parameters:
        - user_id (int): The unique identifier for the user.
        - chat_session_id (int): The identifier for the chat session.
        - generated_chat_title (str): The generated chat title to be saved.
        """
        self.db.chat_history.update_one(
            {"user_id":user_id, "chat_session_id":chat_session_id},
            {"$set":{"chat_title":generated_chat_title}}
        )



    def get_chat_history(self, user_id, chat_session_id):
        """
        Retrieve the raw chat history from the database and format 
        it for response.

        Parameters:
        - user_id (int): The unique identifier for the user.
        - chat_session_id (int): The identifier for the chat session.

        Returns:
        - list: A list containing formatted chat history.

        Raises:
        - NotFound: If the chat history is not found in the database.

        """
            
        # Your chat_history retrieval code
        chat_history = self.db.chat_history.find_one(
            {'user_id': user_id, 'chat_session_id': chat_session_id}
        )

        # Check if chat_history is None
        if chat_history is None:
            raise ValueError("Chat history not found")

        # Parse the 'messages' field from JSON string to a Python list
        messages_json = chat_history.get('messages', '[]')
        messages_list = json.loads(messages_json)

        # Automatically create the desired data structure
        formatted_data = []
        current_human_message = None

        for message in messages_list:
            if message['type'] == 'human':
                if current_human_message:
                    # Add the current_human_message to formatted_data
                    formatted_data.append({"messages": current_human_message})
                
                # Start a new current_human_message list
                current_human_message = [{
                    "content": message['data']['content'],
                    "type": message['type']
                }]
            else:
                if current_human_message is None:
                    current_human_message = []

                # Add the AI message to the current_human_message list
                current_human_message.append({
                    "content": message['data']['content'],
                    "type": message['type']
                })

        # Add the last current_human_message to formatted_data
        if current_human_message:
            formatted_data.append({"messages": current_human_message})
        
        return formatted_data
    
    # define function to get the chat_title
    def get_chat_title(self, user_id, chat_session_id):
        """
        Retrieve the chat title for a specific chat session.

        Args:
        - user_id (int): The unique identifier for the user.
        - chat_session_id (int): The unique identifier for 
        the chat session.

        Returns:
        - str: The chat title for the specified chat session.
        """

        retrieved_chat_title = self.db.chat_history.find_one(
            {"user_id":user_id, "chat_session_id":chat_session_id},
            {"_id":0, "chat_title":1}
        )
        # return the retrived_chat_title
        return retrieved_chat_title.get("chat_title")


    # define the method to rename the chat title
    def rename_chat_title(self, user_id, chat_session_id, chat_title):
        """
        Helper method to update the chat title in the database.

        Args:
        - user_id (int): The ID of the user associated with the
          chat session.
        - chat_session_id (int): The ID of the chat session for
          which the title needs to be updated.
        - chat_title (str): The new chat title.

        Returns:
        - None

        Description:
        This method updates the chat title for a specific chat 
        session in the database.
        It is called by the 'put' method of the ChatTitleRenameResource class.

        Example Usage:
        ```
        chat_title = "New Chat Title"
        resource.rename_chat_title(user_id=1, chat_session_id=123, chat_title=chat_title)
        ```

        """
        # update the chat title from document . 
        self.db.chat_history.update_one(
            {"user_id":user_id, "chat_session_id":chat_session_id},
            {"$set":{"chat_title":chat_title}}
        )

    # define function to check the chat_title existence against the parameters
    def does_chat_title_exist(self, user_id, chat_session_id, chat_title):
        """
        Helper method to check the existence of a chat title in the database.

        Args:
        - user_id (int): The ID of the user associated with the chat session.
        - chat_session_id (int): The ID of the chat session.
        - chat_title (str): The chat title to check for existence.

        Returns:
        - bool: True if the chat title exists, False otherwise.

        Description:
        This method checks whether a specific chat title exists for a given 
        user and chat session in the database.
        It is called by the 'put' method of the ChatTitleRenameResource class
          to validate the input.

        Example Usage:
        ```
        chat_title_exists = resource.does_chat_title_exist(user_id=1, 
        chat_session_id=123, chat_title="Existing Title")
        ```

        """
        chat_title_document = self.db.chat_history.find_one(
            {"user_id":user_id, "chat_session_id":chat_session_id},
            {"_id":0, "chat_title":1}
            )
       
        # return the chat_title_document with (True or False)
        return chat_title_document is not None
    
    # define the function to check the existence of data
    def check_session_existence(self, user_id, chat_session_id):
        """
        Helper method to check the existence of a specific 
        chat session in the database.

        Args:
        - user_id (int): The ID of the user associated with
          the chat session.
        - chat_session_id (int): The ID of the chat session.

        Returns:
        - bool: True if the chat session exists, False otherwise.

        Description:
        This method checks if the specified chat session exists
          in the database.

        Example Usage:
        ```
        chat_session_exists = resource.check_data_existence(
            user_id=1, chat_session_id=123
            )
        ```

        """
        data_exists = self.db.chat_history.find_one(
            {'user_id': user_id, 'chat_session_id': chat_session_id}
            )
        
        return data_exists
    
    # define the function to delete the chat session
    def delete_chat_session(self, user_id, chat_session_id):
        """
        Helper method to delete a specific chat session
          from the database.

        Args:
        - user_id (int): The ID of the user associated 
        with the chat session.
        - chat_session_id (int): The ID of the chat 
        session to be deleted.

        Returns:
        - None

        Description:
        This method deletes the specified chat session
          from the database.

        Example Usage:
        ```
        resource.delete_chat_session(
            user_id=1, chat_session_id=123
            )
        ```

        """
        self.db.chat_history.delete_one(
            {'user_id':user_id, 'chat_session_id':chat_session_id}
            )
        
     # define function to delete the all chats
    def delete_all_chats(self, user_id):
        """
        Helper method to delete all chat sessions 
        for a specific user from the database.

        Args:
        - user_id (int): The ID of the user.

        Returns:
        - None

        Description:
        This method deletes all chat sessions for
          the specified user from the database.

        Example Usage:
        ```
        resource.delete_all_chats(user_id=1)
        ```

        """
        self.db.chat_history.delete_many({'user_id':user_id})
    
    # define function to check the data from database
    def check_user_existence(self, user_id):
        """
        Helper method to check the existence of any 
        chat sessions for a specific user in the database.

        Args:
        - user_id (int): The ID of the user.

        Returns:
        - bool: True if chat sessions exist, False otherwise.

        Description:
        This method checks if any chat sessions exist for the
          specified user in the database.

        Example Usage:
        ```
        chat_sessions_exist = resource.check_data_existence(user_id=1)
        ```

        """
        data_exists = self.db.chat_history.find_one({'user_id':user_id})
        return data_exists

    def get_chat_sessions(self, user_id):
        chat_sessions = self.db.chat_history.distinct(
            "chat_session_id", {"user_id": user_id}
        )
        chat_sessions.sort(reverse=True)  # Sort in descending order
        return chat_sessions

 