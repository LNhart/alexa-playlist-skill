# -*- coding: utf-8 -*-


import random
import logging
import os
import boto3
#import spotipy
#from spotipy.oauth2 import SpotifyOAuth
import requests

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.utils.request_util import get_slot_value, get_locale
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response
from ask_sdk_s3.adapter import S3Adapter



#SKILL_NAME = 'my playlist assistant'
#bucket_name = os.environ.get('S3_PERSISTENCE_BUCKET')
#s3_client = boto3.client('s3',
#                         region_name=os.environ.get('S3_PERSISTENCE_REGION'),
#                         config=boto3.session.Config(signature_version='s3v4',s3={'addressing_style': 'path'}))
#s3_adapter = S3Adapter(bucket_name=bucket_name, path_prefix="Media", s3_client=s3_client)
#sb = CustomSkillBuilder(persistence_adapter=s3_adapter)
sb = CustomSkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#user_playlist_titles = []


@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch.

    Get the persistence attributes, to figure out the game state.
    """
    # type: (HandlerInput) -> Response
    '''
    attr = handler_input.attributes_manager.persistent_attributes
    if not attr:
        attr['ended_session_count'] = 0
        attr['games_played'] = 0
        attr['game_state'] = 'ENDED'

    handler_input.attributes_manager.session_attributes = attr
    
    '''
    
    session_attr = handler_input.attributes_manager.session_attributes
    
    if not session_attr:
        playlist_titles = read_playlists(handler_input)
    
    session_attr["user_playlists"] = playlist_titles
    
    locale = get_locale(handler_input)
    
    #print(locale)
    
    if locale == "de-DE":
        speech_text = "Du hast {} playlists".format(str(len(playlist_titles)))
    else:
        speech_text = "You have {} playlists".format(str(len(playlist_titles)))
    
    
    #handler_input.attributes_manager.persistent_attributes = session_attr
    #handler_input.attributes_manager.save_persistent_attributes()
    
    reprompt = "Sag mir einfach, nach welcher Playlist ich suchen soll."
    
    handler_input.response_builder.speak(speech_text).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    
    locale = get_locale(handler_input)
    if locale == "de-DE":
        speech_text = (
        "Du kannst mit mir nach einer bestimmten Playlist suchen. Sag mir einfach nach welchem Titel ich suchen soll.")
        reprompt = "Versuche nach einer playlist zu suchen."
    else:
        speech_text = (
        "You can ask me to search for a playlist by name and I will tell you if you have that playlist or any similar ones")
        reprompt = "Try searching a playlist."
        

    handler_input.response_builder.speak(speech_text).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda input:
        is_intent_name("AMAZON.CancelIntent")(input) or
        is_intent_name("AMAZON.StopIntent")(input))
def cancel_and_stop_intent_handler(handler_input):
    """Single handler for Cancel and Stop Intent."""
    # type: (HandlerInput) -> Response
    locale = get_locale(handler_input)
    if locale == "de-DE":
        speech_text = "Ich hoffe ich konnte helfen!!"
    else:
        speech_text = "I hope I was able to be helpful!!"
        

    handler_input.response_builder.speak(
        speech_text).set_should_end_session(True)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    """Handler for Session End."""
    # type: (HandlerInput) -> Response
    logger.info(
        "Session ended with reason: {}".format(
            handler_input.request_envelope.request.reason))
    return handler_input.response_builder.response


def read_playlists(handler_input):
    """Function that acts as can handle for game state."""
    # type: (HandlerInput) -> bool
    accessToken = handler_input.request_envelope.context.system.user.access_token
    
    headers = {
    'Authorization': 'Bearer {token}'.format(token=accessToken)
    }
    
    # base URL of all Spotify API endpoints
    BASE_URL = 'https://api.spotify.com/v1/'
    
    
    user_r = requests.get(BASE_URL + "me/playlists", headers=headers)
    
    playlists = user_r.json()["items"]
    
    playlist_titles = []
    
    for item in playlists:
        playlist_titles.append(item["name"].lower())
        
    return playlist_titles


def calculate_distance(term_1, term_2):
    match_1 = 0
    match_2 = 0
    
    for term in term_1.split(" "):
        if term in term_2:
            match_1 += 1
            
    for term in term_2.split(" "):
        if term in term_1:
            match_2 += 1
            
    if match_1 > match_2:
        return match_1
    else:
        return match_2

#@sb.request_handler(can_handle_func=lambda input:
#                    not currently_playing(input) and
#                    is_intent_name("AMAZON.YesIntent")(input))
#def yes_handler(handler_input):
#    """Handler for Yes Intent, only if the player said yes for
#    a new game.
#    """
#    # type: (HandlerInput) -> Response
#    session_attr = handler_input.attributes_manager.session_attributes
#    session_attr['game_state'] = "STARTED"
#    session_attr['guess_number'] = random.randint(0, 100)
#    session_attr['no_of_guesses'] = 0
#
#    speech_text = "Great! Try saying a number to start the game."
#    reprompt = "Try saying a number."
#
#    handler_input.response_builder.speak(speech_text).ask(reprompt)
#    return handler_input.response_builder.response
#
#
#@sb.request_handler(can_handle_func=lambda input:
#                    not currently_playing(input) and
#                    is_intent_name("AMAZON.NoIntent")(input))
#def no_handler(handler_input):
#    """Handler for No Intent, only if the player said no for
#    a new game.
#    """
#    # type: (HandlerInput) -> Response
#    session_attr = handler_input.attributes_manager.session_attributes
#    session_attr['game_state'] = "ENDED"
#    session_attr['ended_session_count'] += 1
#
#    handler_input.attributes_manager.persistent_attributes = session_attr
#    handler_input.attributes_manager.save_persistent_attributes()
#
#    speech_text = "Ok. See you next time!!"
#
#    handler_input.response_builder.speak(speech_text)
#    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=lambda input:
                    is_intent_name("SearchMyPlaylistIntent")(input))
def number_guess_handler(handler_input):
    """Handler for processing guess with target."""
    
    
    session_attr = handler_input.attributes_manager.session_attributes
    if session_attr:
        user_playlist_titles = session_attr["user_playlists"]
    else:
        user_playlist_titles = read_playlists(handler_input)
        session_attr["user_playlists"] = user_playlist_titles
    
    #search_name = handler_input.request_envelope.request.intent.slots[
    #    "playlist_name"]["value"]
    query_name = get_slot_value(handler_input, "playlist_name").lower()
    
    #print(search_name)
    locale = get_locale(handler_input)
    
    exact_match = False
    
    match_list = []
    
    if query_name in user_playlist_titles:
        exact_match = True
    else:
        for title in user_playlist_titles:
            dist = calculate_distance(query_name, title)
            if dist > 0:
                match_list.append((title, dist))
    
    dist_sorted = sorted(match_list, key=lambda x : x[1])
    
    relevant_matches = []
    
    print(dist_sorted)
    
    if len(dist_sorted) > 0 :
        top_match = dist_sorted[0][1]
        i = 0
        for item in dist_sorted:
            if item[1] == top_match:
                relevant_matches.append(item[0])
                i += 1
            else:
                break
            if i > 6:
                break
    
    
    if exact_match:
        if locale == "de-DE":
            speech_text = "Diese Playlist hast du, der genaue Name ist: " + query_name
        else:
            speech_text = "This playlist exists, the exact name is: " + query_name
    elif len(relevant_matches) > 0:
        if locale == "de-DE":
            speech_text = "Du hast diese playlists mit einem ähnlichen Namen: " + ", ".join(relevant_matches) + "."
        else:
            speech_text = "You have some playlists with a similar name: " + ", ".join(relevant_matches) + "."
    else:
        if locale == "de-DE":
            speech_text = "Tut mir leid, ich habe leider nichts, was dazu passt."
        else:
            speech_text = "Sorry, I couldn't find anything like that."
        
    #reprompt = "Can you repeat that please?"

    
    handler_input.response_builder.speak(speech_text)#.ask(reprompt)
    return handler_input.response_builder.response


#@sb.request_handler(can_handle_func=lambda input:
#                    is_intent_name("AMAZON.FallbackIntent")(input) or
#                    is_intent_name("AMAZON.YesIntent")(input) or
#                    is_intent_name("AMAZON.NoIntent")(input))
#def fallback_handler(handler_input):
#    """AMAZON.FallbackIntent is only available in en-US locale.
#    This handler will not be triggered except in that locale,
#    so it is safe to deploy on any locale.
#    """
#    # type: (HandlerInput) -> Response
#    session_attr = handler_input.attributes_manager.session_attributes
#
#    
#    speech_text = (
#            "The {} skill can't help you with that.  "
#            "Try searching for a playlist by name ".format(SKILL_NAME))
#    reprompt = "Please tell me what playlist to search for."
#    
#
#    handler_input.response_builder.speak(speech_text).ask(reprompt)
#    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=lambda input: True)
def unhandled_intent_handler(handler_input):
    """Handler for all other unhandled requests."""
    # type: (HandlerInput) -> Response
    locale = get_locale(handler_input)
    if locale == "de-DE":
        speech = "Ich bin mir nicht ganz sicher, was du meinst. Bitte suche nach einer playlist."
    else:
        speech = "I am not quite sure how to deal with that. Please try to search for a playlist."
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    # type: (HandlerInput, Exception) -> Response
    logger.error(exception, exc_info=True)
    locale = get_locale(handler_input)
    if locale == "de-DE":
        speech = "Sorry, das habe ich nicht verstanden. Bitte versuche es noch einmal."
    else:
        speech = "Sorry, I can't understand that. Please say again!!"
    
        
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response


@sb.global_response_interceptor()
def log_response(handler_input, response):
    """Response logger."""
    # type: (HandlerInput, Response) -> None
    logger.info("Response: {}".format(response))


lambda_handler = sb.lambda_handler()
