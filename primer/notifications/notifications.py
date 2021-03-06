import re
from datetime import datetime

from django.contrib import messages
from django.template.loader import select_template, TemplateDoesNotExist

from primer.push.services import PushService
from primer.notifications.models import NotificationStore, UserNotification
from primer.utils import get_request


def push_count_update(user):
    """
    Pushes a count update to all of the clients machines
    """
    if PushService:
        count = UserNotification.objects.filter(user = user, read = False).count()
        PushService.send('notification.count', users = user, data = {'count' : count})


class Notification:

    store = 1
    users = []
    sender = None,
    type = None
    tags = ''
    message = ''
    data = None
    push = False

    def __init__(self, users = None, *args, **kwargs):
        """
        Init takes the following additional properties
        - store: storage level 0 - 2
        - user: a single user to link this notification to
        - users: a list or qs of users to link this notificaiton to
        """
        
        self.store = kwargs.get('store', self.store)
        self.message = kwargs.get('message', self.message)
        self.type = kwargs.get('type', self.type)
        self.tags = kwargs.get('tags', self.tags)
        self.sender = kwargs.get('sender', self.sender)
        self.data = kwargs.get('data', self.data)
        self.push = kwargs.get('push', self.push)

        # handle passing in a single user or multiple users
        self.users = kwargs.get('users', self.users)
        if not hasattr(self.users, '__iter__'):
            self.users = [self.users]
        
        # if the type is not set, set it dynamically based on the class name
        if not self.type:
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', self.__class__.__name__)
            self.type = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()



    def get_target(self):
        """
        This method should return either a link, or something the djangos urlresolvers reverse can turn into a link
        This gets called right before save, so it should have access to the rest of the models attributes
        """
        return None


    def template(self):
        """
        Gets the template for the notification
        """
        type_name = self.type.replace('-','_')
        
        template = select_template([
            'notifications/display/%s.html' % type_name,
            'notifications/display/default.html'
            ])

        return template.name



    def send(self):
        """
        Send and or save the actual notification
        """ 
        request = get_request()
        self.tags = '%s %s' % (self.tags, self.type)

        # if we still dont have any users, set it to the user in the request.
        # We do it here and not in model init to avoid redundant calls to get_request
        # when we might be saving the model directly
        if not len(self.users):
            self.users = [request.user]

        # if the store option is 1 or 2, we will store the notification
        if self.store == 1 or self.store == 2:
            
            # start by saving the actual notification
            notification = NotificationStore(
                message = self.message,
                target = self.get_target(),
                type = self.type,
                sender = self.sender,
                data = self.data
                ).save()

            # loop through and create following links for users
            followers_to_save = []
            for user in self.users:

                # catch if is is an unauthenticated user, we wont save
                if user == request.user and not request.user.is_authenticated():
                    continue
                else:
                    followers_to_save.append(UserNotification(user = user, notification = notification))

            # bulk save the user links
            UserNotification.objects.bulk_create(followers_to_save)

            # update the users notification counts
            for user in self.users:
                push_count_update(user)


        # here we check to see that the notification should actually be sent, which is any storage level except 2
        if self.store != 2:

            for user in self.users:

                # push our notification is push is set to true and we have a push service
                if self.push and PushService:

                    # here we have a user making a request that is not ajax and the push notification is supposed to go to them
                    # it will never make it there because of the page request, so just catch it and send it through normally
                    if not request.is_ajax() and user == request.user:
                        messages.add_message(request, messages.INFO, self, extra_tags = self.tags)
                    else:
                        
                        # we will send through our arbitrary data with the message
                        push_data = {'message' : self.message, 'tags' : self.tags}
                        if self.data: push_data.update(self.data)

                        PushService.send(
                            event = 'notification.new-notification', 
                            data = push_data,
                            users = user
                            )

                else:
                    if user == request.user:
                        messages.add_message(request, messages.INFO, self, extra_tags = self.tags)

                    


    def __unicode__(self):
        return self.message


class SuccessNotification(Notification):
    tags = 'alert-success'
    store = 0


class ErrorNotification(Notification):
    tags = 'alert-error'
    store = 0


class InfoNotification(Notification):
    tags = 'alert-info'
    store = 0


class WarningNotification(Notification):
    tags = 'alert-warning'
    store = 0