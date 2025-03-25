# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from consultations.models import Consultation
# from django.utils import timezone
# from .models import ChatMessage
# from credits.models import UserCredit, ProviderCredit, Transaction
# from channels.layers import get_channel_layer
# from django.core.exceptions import ObjectDoesNotExist
# from django.db import transaction
# import asyncio


# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
#         self.room_group_name = f'consultation_{self.consultation_id}'

#         #Join the room
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()

#         await self.send_chat_history()

#     async def disconnect(self, close_code):
#         #Leave the room
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#         #Strop credit tracking task if it is running
#         if hasattr(self, 'track_credits_task') and self.track_credits_task is not None:
#             self.track_credits_task.cancel()
    
#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message_type = text_data_json.get('type')

#         if message_type == 'chat_message':
#             message = text_data_json.get('message')
#             await self.handle_chat_message(message)
#         # We receive the consultation end request via the view
#         # So, we handle it from a seperate method

#     async def handle_chat_message(self, message_text):
#         """Handles a received chat message"""
#         consultation = await self.get_consultation()
#         if not consultation:
#             return # Or handle the error appropriately

#         if self.scope["user"] != consultation.user and self.scope["user"] != consultation.provider.user:
#             return  # Or send an error message
        
#         # Create and save the chat message (store the whole message)
#         message = await self.save_message(message_text)

#         # Send message to group
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',  # The method name to call on the consumer
#                 'message': message, # The message itself
#             }
#         )
#         print(f"CHAT MESSAGE: User: {self.scope['user'].email}, Message: {message_text}")

#     async def consultation_accepted(self, event):
#         """Handles the 'consultation.accepted' event."""
#         consultation_id = event['consultation_id']
#         # Only start tracking if *this* consumer's consultation is the one accepted
#         if int(self.consultation_id) == consultation_id:  # Ensure correct consultation
#               consultation = await self.get_consultation()
#               if consultation and consultation.status == Consultation.ACCEPTED: #Check if the consultation is accepted
#                     await self.set_consultation_status(Consultation.ONGOING)
#                     await self.start_credit_tracking()
#                     # Send a message to the client
#                     await self.send(text_data=json.dumps({
#                         'type': 'consultation_status',
#                         'status': 'ongoing',
#                     }))
#                     print(f"CONSULTATION STARTED (consumer): {consultation.user.email} - {consultation.provider.user.email}")

#     async def consultation_cancelled(self, event):
#         consultation_id = event['consultation_id']
#         if int(self.consultation_id) == consultation_id:  # Ensure correct consultation
#             consultation = await self.get_consultation()
#             if not consultation:
#                  return
#             # Stop credit tracking, if ongoing
#             if hasattr(self, 'track_credits_task') and self.track_credits_task is not None:
#                 self.track_credits_task.cancel()
#             # Send message
#             await self.send(text_data=json.dumps({
#                 'type': 'consultation_status',
#                 'status': 'cancelled'
#             }))
#             print(f"CONSULTATION CANCELLATION (consumer): {consultation.user.email} - {consultation.provider.user.email}")
#             await self.close()

#     async def start_credit_tracking(self):
#         """Starts a background task to track credits."""
#         self.track_credits_task = self.channel_layer.send(
#             "track-credits",  # Special channel name for background tasks
#             {
#                 "type": "track.credits",
#                 "consultation_id": self.consultation_id,
#                 "room_group_name": self.room_group_name,
#             }
#         )

#     async def track_credits(self, event):
#         """
#         Background task to periodically check and update credits.
#         This runs in a separate task, not in the main consumer thread.
#         """
#         consultation_id = event["consultation_id"]
        
#         while True:  # Run indefinitely (until stopped)
#             consultation = await self.get_consultation()
#             if consultation is None:
#                 break #If consultation gets deleted somehow
            
#             if consultation.status != Consultation.ONGOING:
#                 break # Stop if not ongoing

#             # Calculate elapsed time and cost
#             elapsed_time = timezone.now() - consultation.start_time
#             duration_minutes = elapsed_time.total_seconds() / 60
#             cost = round(duration_minutes * consultation.provider.rate_per_minute, 2)

#             # Get user credit and check balance
#             user_credit = await self.get_user_credit(consultation.user)
            
#             if user_credit is None:
#                  break # If User credit gets deleted somehow

#             # Send credit update to the group (both user and provider)
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'credit_update',
#                     'credits': str(user_credit.balance - cost),  # Send as string for JSON
#                 }
#             )
#             print(f"Current cost: {cost}, Remaining Balance: {user_credit.balance - cost}")

#             if user_credit.balance < cost:
#                 await self.channel_layer.group_send(
#                     self.room_group_name,
#                     {
#                         'type': 'credit_depleted',
#                         'message': 'Insufficient credits. Ending consultation.'
#                     }
#                 )
#                 print(f"CREDITS DEPLETED: {consultation.user.email} - {consultation.provider.user.email}")
#                 # End the consultation automatically
#                 await self.end_consultation_from_credit_depletion()
#                 break #Exit loop

#             await asyncio.sleep(20)  # Check every 20 seconds (adjust as needed)

#     async def credit_update(self, event):
#         """
#         Handler for credit update messages. Sends the update to the WebSocket.
#         """
#         await self.send(text_data=json.dumps({
#             'type': 'credit_update',
#             'credits': event['credits'],
#         }))

#     async def credit_depleted(self, event):
#          await self.send(text_data=json.dumps({
#               'type': 'credit_depleted',
#               'message': event['message'],
#          }))

    
#     async def end_consultation_from_credit_depletion(self):
#         # This method is nearly identical to end_consultation, but it's
#         # triggered internally by credit depletion, not by a user action.
#         consultation = await self.get_consultation()
#         if consultation.status != Consultation.ONGOING:
#             return

#         await self.perform_final_credit_deduction(consultation)
#         await self.set_consultation_status(Consultation.COMPLETED)

#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'consultation_ended',
#                 'message': 'Consultation ended due to insufficient credits.'
#             }
#         )
#         print(f"AUTO-ENDED (credits): {consultation.user.email} - {consultation.provider.user.email}")
#         await self.close()


#     async def consultation_end(self, event):
#         consultation_id = event["consultation_id"]

#         # Only proceed if this consumer is for the correct consultation
#         if int(self.consultation_id) == consultation_id:
#             consultation = await self.get_consultation()

#             # Stop credit tracking, if running
#             if hasattr(self, 'track_credits_task') and self.track_credits_task is not None:
#                 self.track_credits_task.cancel()

#             # Perform final credit deduction and update status
#             if consultation and consultation.status == Consultation.ONGOING:
#                 await self.perform_final_credit_deduction(consultation)
#                 await self.set_consultation_status(Consultation.COMPLETED)

#                 # Notify clients
#                 await self.channel_layer.group_send(
#                     self.room_group_name,
#                     {
#                         'type': 'consultation_ended',
#                         'message': 'Consultation ended successfully.'
#                     }
#                 )
#                 print(f"CONSULTATION ENDED (consumer): {consultation.user.email} - {consultation.provider.user.email}")

#                 await self.close()
    
#     async def consultation_ended(self, event):
#         """Handles the 'consultation.ended' event."""
#         await self.send(text_data=json.dumps({
#             'type': 'consultation_ended',
#             'message': event['message']
#         }))

#     async def send_chat_history(self):
#         messages = await self.get_chat_history()
#         await self.send(text_data=json.dumps({
#             'type': 'chat_history',
#             'messages': messages
#         }))

#     # --- Helper methods (database interactions) ---

#     @database_sync_to_async
#     def get_consultation(self):
#         try:
#             return Consultation.objects.get(pk=self.consultation_id)
#         except Consultation.DoesNotExist:
#             return None
        
#     @database_sync_to_async
#     def get_user_credit(self, user):
#         try:
#             return UserCredit.objects.get(user=user)
#         except ObjectDoesNotExist:
#             return None
    
#     @database_sync_to_async
#     def set_consultation_status(self, status):
#         consultation = self.get_consultation()
#         if consultation:
#              consultation.status = status
#              if status == Consultation.ONGOING and consultation.start_time is None:
#                  consultation.start_time = timezone.now() # Set start_time if not already set
#              consultation.save()

#     @database_sync_to_async
#     def save_message(self, message_text):
#         consultation = self.get_consultation()
#         if consultation:
#             message = ChatMessage.objects.create(
#                 consultation=consultation,
#                 sender=self.scope["user"],
#                 message={'text': message_text}  # Store as JSON
#             )
#             return {
#                 'id': message.id,
#                 'sender': message.sender.email,
#                 'message': message.message,
#                 'timestamp': message.timestamp.isoformat()  # Serialize datetime
#             }
    
#     @database_sync_to_async
#     def get_chat_history(self):
#         messages = ChatMessage.objects.filter(consultation_id=self.consultation_id).order_by('timestamp')
#         return [
#             {
#                 'id': msg.id,
#                 'sender': msg.sender.email,
#                 'message': msg.message,
#                 'timestamp': msg.timestamp.isoformat()
#             } for msg in messages
#         ]
    
#     @database_sync_to_async
#     @transaction.atomic
#     def perform_final_credit_deduction(self, consultation):
#         """Performs the final credit deduction and updates balances."""
#         consultation.refresh_from_db() # Ensure you have the latest data, prevents race condition.
#         consultation.end_time = timezone.now()
#         duration_minutes = (consultation.end_time - consultation.start_time).total_seconds() / 60
#         cost = round(duration_minutes * consultation.provider.rate_per_minute, 2)

#         user_credit, _ = UserCredit.objects.get_or_create(user=consultation.user)
#         provider_credit, _ = ProviderCredit.objects.get_or_create(provider=consultation.provider)

#         if cost > 0:
#             Transaction.objects.create(
#                 user=consultation.user,
#                 amount=cost,
#                 transaction_type=Transaction.CONSULTATION,
#                 status=Transaction.SUCCESS,
#                 description=f"Consultation with {consultation.provider.user.email}",
#             )

#             user_credit.balance -= cost
#             user_credit.save()

#             provider_credit.balance += cost
#             provider_credit.save()

#     # --- Message Handlers (for group messages) ---
#     async def chat_message(self, event):
#         """Handles incoming chat messages from the group."""
#         message = event['message']
#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({
#             'type': 'chat_message',
#             'message': message,
#         }))

        


import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async 
# from consultations.models import Consultation <-- NO TOP-LEVEL IMPORTS OF MODELS
# from .models import ChatMessage
# from credits.models import UserCredit, ProviderCredit, Transaction
from django.utils import timezone
from channels.layers import get_channel_layer
import asyncio



class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.room_group_name = f'consultation_{self.consultation_id}'

        await self.accept()
        

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # Stop the credit tracking task, if it's running
        if hasattr(self, 'track_credits_task') and self.track_credits_task is not None:
            self.track_credits_task.cancel()


    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        # --- CUSTOM TOKEN AUTHENTICATION ---
        if message_type == 'authenticate':
            token = text_data_json.get('token')
            await self.authenticate_user(token)  # New authentication method
            return  # Important:  Process *only* the auth message.
        # --- END CUSTOM TOKEN AUTHENTICATION ---

        if message_type == 'chat_message':
            message = text_data_json.get('message')
            await self.handle_chat_message(message)
        # We receive the consultation end request via the view
        # So, we handle it from a seperate method
    
    async def authenticate_user(self, token):
        """Custom authentication method."""
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError  
        from rest_framework_simplejwt.tokens import AccessToken
        try:
            # Manually validate the token
            validated_token = AccessToken(token)
            user_id = validated_token['user_id']  # Extract user_id

            # Get the user (database operation, so use sync_to_async)
            user = await self.get_user(user_id)

            if user:
                self.scope['user'] = user  # Manually set the user in the scope
                print(f"Authenticated user: {user.email}")

                # Join room group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )

                 # Send chat history (if any)
                await self.send_chat_history()            

            else:
                print("Authentication failed: User not found")
                await self.send(text_data=json.dumps({
                    'type': 'authentication_result',
                    'status': 'failed',
                    'message': 'Invalid user.'
                }))
                await self.close(code=4001)

        except (InvalidToken, TokenError) as e:
            print(f"Authentication failed: {e}")
            await self.send(text_data=json.dumps({
                'type': 'authentication_result',
                'status': 'failed',
                'message': 'Invalid token.'
            }))
            await self.close(code=4001)  # Close connection on invalid token
        except Exception as e:
            print(f"An unexpected error occurred during authentication: {e}")
            await self.send(text_data=json.dumps({
                'type': 'authentication_result',
                'status': 'failed',
                'message': 'An unexpected error occurred.'
            }))
            await self.close(code=4999)


    async def handle_chat_message(self, message_text):
        """Handles a received chat message."""
        from channels.db import database_sync_to_async # Import here
        consultation = await self.get_consultation()
        if not consultation:
            return # Or handle the error appropriately

        is_participant = await self.check_participation(consultation)
        if not is_participant:
            return  # Or send an error

        # Create and save the chat message (store the whole message)
        message = await self.save_message(message_text)

        # Send message to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',  # The method name to call on the consumer
                'message': message, # The message itself
            }
        )
        print(f"CHAT MESSAGE: User: {self.scope['user'].email}, Message: {message_text}")

    async def consultation_accepted(self, event):
        """Handles the 'consultation.accepted' event."""
        from channels.db import database_sync_to_async
        consultation_id = event['consultation_id']
        # Only start tracking if *this* consumer's consultation is the one accepted
        if int(self.consultation_id) == consultation_id:  # Ensure correct consultation
              consultation = await self.get_consultation()
              if consultation and consultation.status == "accepted": #Check if the consultation is accepted
                    await self.set_consultation_status("ongoing")
                    await self.start_credit_tracking()
                    # Send a message to the client
                    await self.send(text_data=json.dumps({
                        'type': 'consultation_status',
                        'status': 'ongoing',
                    }))
                    print(f"CONSULTATION STARTED (consumer): {consultation.user.email} - {consultation.provider.user.email}")

    async def consultation_cancelled(self, event):
        consultation_id = event['consultation_id']
        if int(self.consultation_id) == consultation_id:  # Ensure correct consultation
            consultation = await self.get_consultation()
            if not consultation:
                 return
            # Stop credit tracking, if ongoing
            if hasattr(self, 'track_credits_task') and self.track_credits_task is not None:
                self.track_credits_task.cancel()
            # Send message
            await self.send(text_data=json.dumps({
                'type': 'consultation_status',
                'status': 'cancelled'
            }))
            print(f"CONSULTATION CANCELLATION (consumer): {consultation.user.email} - {consultation.provider.user.email}")
            await self.close()

    async def start_credit_tracking(self):
        """Starts a background task to track credits."""
        self.track_credits_task = self.channel_layer.send(
            "track-credits",  # Special channel name for background tasks
            {
                "type": "track.credits",
                "consultation_id": self.consultation_id,
                "room_group_name": self.room_group_name,
            }
        )

    async def track_credits(self, event):
        """
        Background task to periodically check and update credits.
        This runs in a separate task, not in the main consumer thread.
        """
        from channels.db import database_sync_to_async
        from consultations.models import Consultation #Local import
        consultation_id = event["consultation_id"]
        
        while True:  # Run indefinitely (until stopped)
            consultation = await self.get_consultation()
            if consultation is None:
                break #If consultation gets deleted somehow
            
            if consultation.status != Consultation.ONGOING:
                break # Stop if not ongoing

            # Calculate elapsed time and cost
            elapsed_time = timezone.now() - consultation.start_time
            duration_minutes = elapsed_time.total_seconds() / 60
            cost = round(duration_minutes * consultation.provider.rate_per_minute, 2)

            # Get user credit and check balance
            user_credit = await self.get_user_credit(consultation.user)
            
            if user_credit is None:
                 break # If User credit gets deleted somehow

            # Send credit update to the group (both user and provider)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'credit_update',
                    'credits': str(user_credit.balance - cost),  # Send as string for JSON
                }
            )
            print(f"Current cost: {cost}, Remaining Balance: {user_credit.balance - cost}")

            if user_credit.balance < cost:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'credit_depleted',
                        'message': 'Insufficient credits. Ending consultation.'
                    }
                )
                print(f"CREDITS DEPLETED: {consultation.user.email} - {consultation.provider.user.email}")
                # End the consultation automatically
                await self.end_consultation_from_credit_depletion()
                break #Exit loop

            await asyncio.sleep(5)  # Check every 5 seconds (adjust as needed)

    async def credit_update(self, event):
        """
        Handler for credit update messages. Sends the update to the WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'credit_update',
            'credits': event['credits'],
        }))

    async def credit_depleted(self, event):
         await self.send(text_data=json.dumps({
              'type': 'credit_depleted',
              'message': event['message'],
         }))

    async def end_consultation_from_credit_depletion(self):
        # This method is nearly identical to end_consultation, but it's
        # triggered internally by credit depletion, not by a user action.
        from channels.db import database_sync_to_async
        consultation = await self.get_consultation()
        if consultation.status != "ongoing":
            return

        await self.perform_final_credit_deduction(consultation)
        await self.set_consultation_status("completed")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'consultation_ended',
                'message': 'Consultation ended due to insufficient credits.'
            }
        )
        print(f"AUTO-ENDED (credits): {consultation.user.email} - {consultation.provider.user.email}")
        await self.close()

    async def consultation_end(self, event):
        from channels.db import database_sync_to_async
        consultation_id = event["consultation_id"]

        # Only proceed if this consumer is for the correct consultation
        if int(self.consultation_id) == consultation_id:
            consultation = await self.get_consultation()

            # Stop credit tracking, if running
            if hasattr(self, 'track_credits_task') and self.track_credits_task is not None:
                self.track_credits_task.cancel()

            # Perform final credit deduction and update status
            if consultation and consultation.status == "ongoing":
                await self.perform_final_credit_deduction(consultation)
                await self.set_consultation_status("completed")

                # Notify clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'consultation_ended',
                        'message': 'Consultation ended successfully.'
                    }
                )
                print(f"CONSULTATION ENDED (consumer): {consultation.user.email} - {consultation.provider.user.email}")

                await self.close()

    async def consultation_ended(self, event):
        """Handles the 'consultation.ended' event."""
        await self.send(text_data=json.dumps({
            'type': 'consultation_ended',
            'message': event['message']
        }))

    async def send_chat_history(self):
        messages = await self.get_chat_history()
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': messages
        }))

    # --- Helper methods (database interactions) ---
    @database_sync_to_async
    def get_user(self, user_id):
        from users.models import User
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def check_participation(self, consultation):
        """Checks if the current user is part of the consultation."""
        return self.scope["user"] == consultation.user or self.scope["user"] == consultation.provider.user
        
    @database_sync_to_async
    def get_consultation(self):
        from consultations.models import Consultation # Local import
        try:
            return Consultation.objects.get(pk=self.consultation_id)
        except Consultation.DoesNotExist:
            return None
        
    @database_sync_to_async
    def get_user_credit(self, user):
        from credits.models import UserCredit # Local Import
        from django.core.exceptions import ObjectDoesNotExist # Local Import
        try:
            return UserCredit.objects.get(user=user)
        except ObjectDoesNotExist:
            return None
        
    @database_sync_to_async
    def set_consultation_status(self, status):
        from consultations.models import Consultation
        from django.utils import timezone
        consultation = self.get_consultation()
        if consultation:
             consultation.status = status
             if status == Consultation.ONGOING and consultation.start_time is None:
                 consultation.start_time = timezone.now() # Set start_time if not already set
             consultation.save()

    @database_sync_to_async
    def save_message(self, message_text):
        from .models import ChatMessage
        from consultations.models import Consultation

        consultation = Consultation.objects.get(pk=self.consultation_id)
        if consultation:
            message = ChatMessage.objects.create(
                consultation=consultation,
                sender=self.scope["user"],
                message={'text': message_text}  # Store as JSON
            )
            return {
                'id': message.id,
                'sender': message.sender.email,
                'message': message.message,
                'timestamp': message.timestamp.isoformat()  # Serialize datetime
            }

    @database_sync_to_async
    def get_chat_history(self):
        from .models import ChatMessage
        messages = ChatMessage.objects.filter(consultation_id=self.consultation_id).order_by('timestamp')
        return [
            {
                'id': msg.id,
                'sender': msg.sender.email,
                'message': msg.message,
                'timestamp': msg.timestamp.isoformat()
            } for msg in messages
        ]

    @database_sync_to_async
    def perform_final_credit_deduction(self, consultation):
        """Performs the final credit deduction and updates balances."""
        from credits.models import UserCredit, ProviderCredit, Transaction
        from django.utils import timezone
        consultation.refresh_from_db() # Ensure you have the latest data, prevents race condition.
        consultation.end_time = timezone.now()
        duration_minutes = (consultation.end_time - consultation.start_time).total_seconds() / 60
        cost = round(duration_minutes * consultation.provider.rate_per_minute, 2)

        user_credit, _ = UserCredit.objects.get_or_create(user=consultation.user)
        provider_credit, _ = ProviderCredit.objects.get_or_create(provider=consultation.provider)

        if cost > 0:
            Transaction.objects.create(
                user=consultation.user,
                amount=cost,
                transaction_type=Transaction.CONSULTATION,
                status=Transaction.SUCCESS,
                description=f"Consultation with {consultation.provider.user.email}",
            )

            user_credit.balance -= cost
            user_credit.save()

            provider_credit.balance += cost
            provider_credit.save()

    # --- Message Handlers (for group messages) ---
    async def chat_message(self, event):
        """Handles incoming chat messages from the group."""
        message = event['message']
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
        }))
