#!/usr/bin/python3
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Tuple
import requests
from datetime import datetime

from classes.Profile import Profile
from classes.types.OpseAddress import OpseAddress
from classes.types.OpseLocation import OpseLocation
from tools.Tool import Tool

from utils.config.Config import Config
from utils.datatypes import DataTypeInput
from utils.datatypes import DataTypeOutput
from utils.stdout import print_debug, print_error, print_warning


class DeathTool(Tool):
    """
    Class which describe a DeathTool
    """
    deprecated = False

    def __init__(self):
        """The constructor of a DeathTool"""
        super().__init__()

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Function which return tool configuration as a dictionnary."""
        return {
            'active': True,
        }

    @staticmethod
    def get_lst_input_data_types() -> Dict[str, bool]:
        """
        Function which return the list of data types which can be use to run this Tool.
        It's will help to make decision to run Tool depending on current data.
        """
        return {
            DataTypeInput.FIRSTNAME: True,
            DataTypeInput.MIDDLENAME: False,
            DataTypeInput.LASTNAME: True,
            DataTypeInput.AGE: False,
            DataTypeInput.BIRTHDATE: False,
            DataTypeInput.DEATHDATE: False,
            DataTypeInput.ADRESSE: False,
            DataTypeInput.GENDER: False
        }

    @staticmethod
    def get_lst_output_data_types() -> List[str]:
        """
        Function which return the list of data types which can be receive by using this Tool.
        It's will help to make decision to complete profile to get more information.
        """
        return [
            DataTypeOutput.FIRSTNAME,
            DataTypeOutput.MIDDLENAME,
            DataTypeOutput.LASTNAME,
            DataTypeOutput.AGE,
            DataTypeOutput.BIRTHDATE,
            DataTypeOutput.DEATHDATE,
            DataTypeOutput.ADDRESS,
            DataTypeOutput.GENDER
        ]

    def execute(self):

        firstname = str(self.get_default_profile().get_firstname())
        lastname = str(self.get_default_profile().get_lastname())

        death_results: List[dict] = self.list_deads(firstname, lastname)

        # Create a profile for each Death account found
        # because each account might be a different person
        strict = Config.is_strict()
        for dead in death_results:
            profile: Profile = self.get_default_profile().clone()
            if not strict:
                profile.set_firstname(dead.get('firstname'))
                profile.set_lastname(dead.get('lastname'))
            profile.set_lst_middlenames(dead.get('lst_middlenames'))
            profile.set_gender(dead.get('gender'))
            profile.set_age(dead.get('age'))
            profile.set_lst_locations(dead.get('lst_locations'))
            profile.set_birthdate(dead.get('birthdate'))
            profile.set_birth_address(dead.get('birthaddr'))
            profile.set_deathdate(dead.get('deathdate'))
            profile.set_death_address(dead.get('deathaddr'))

            self.append_profile(profile)

    def list_deads_death_between(self, firstname: str, lastname: str, year_range: Tuple[int, int]) -> list:
        deads = []

        try:
            start = year_range[0]
            end = year_range[1]

            if start < 1886:
                raise ValueError

            if end > date.today().year:
                raise ValueError

            if start > end:
                raise ValueError
        except:
            print_error()

        for date in range(year_range):
            deads.extend(self.list_deads(firstname, lastname, deathdate=date))

        return deads

    def list_deads(self, firstname: str, lastname: str,
        sex: str = "",
        birthdate: str = "",
        birthcity: str = "",
        birthdpt: str = "",
        birthcountry: str = "",
        deathdate: str = "",
        deathage: str = "",
        deathcity: str = "",
        deathdpt: str = "",
        deathcountry: str = "",
    ) -> list:
        """
        Function to list french companies matching firstname and lastname
        """

        url = "https://deces.matchid.io/deces/api/v1/search"

        payload = {
            "fuzzy": "true",
            "sort": [{"score":"desc"}],
            "page": 1,
            "size": 1000,
            "scroll": "1m",
            "lastName": lastname,
            "firstName": firstname,
            "sex": sex,
            "birthDate": birthdate,
            "birthCity": birthcity,
            "birthDepartment": birthdpt,
            "birthCountry": birthcountry,
            "deathDate": deathdate,
            "deathAge": deathage,
            "deathCity": deathcity,
            "deathDepartment": deathdpt,
            "deathCountry": deathcountry
        }

        for key in payload.copy().keys():
            if payload[key] == "":
                payload.pop(key)

        # Try to get the listing page with deads matching Firstname Lastname and more
        try:
            r = requests.post(url=url, json=payload)
            res_json = r.json()
            print_debug("Deces.io request succeed with a " + str(r.status_code) + " status code.")
        except Exception as e:
            print_error("[DeathTool:list_deads] Request failed: " + str(e)[:100], True)
            return None

        # Search in the JSON result for match with firstname and lastname
        deads = []
        if res_json.get('response', []) != []:

            # Here are all the information about the matching deads
            # In the rest of the script, we reduce those information
            lst_deads: List[dict] = res_json['response'].get('persons', [])
            print_debug("Found " + str(len(lst_deads)) + " match"
                + ("es" if len(lst_deads) > 1 else "") + " for " + firstname.capitalize()
                + " " + lastname.capitalize() + " in a fuzzy search.")

            if len(lst_deads) > 0:
                strict = Config.is_strict()
                # Foreach dead found...
                for dead in lst_deads:

                    d_firstname = dead.get('name', {}).get('first', [""])[0]
                    d_lastname = dead.get('name', {}).get('last', "")

                    add_dead = False
                    if strict:
                        if firstname.lower() == d_firstname.lower() and lastname.lower() == d_lastname.lower():
                            add_dead = True
                    else:
                        add_dead = True

                    if add_dead:
                        deads.append({
                            'firstname': d_firstname,
                            'lastname': d_lastname,
                            'lst_middlenames': dead.get('name', {}).get('first', ["", ""])[1:],
                            'gender': dead.get('sex', ""),
                            'age': dead.get('death', {}).get('age', 0),
                            'lst_locations': [
                                OpseLocation(
                                    latitude = dead.get('birth', {}).get('location', {}).get('latitude', None),
                                    longitude = dead.get('birth', {}).get('location', {}).get('longitude', None),
                                    data_source = "https://deces.matchid.io",
                                    data_source_help_text = "",
                                    data_source_help_url = "https://deces.matchid.io/about"
                                ),
                                OpseLocation(
                                    latitude = dead.get('death', {}).get('location', {}).get('latitude', None),
                                    longitude = dead.get('death', {}).get('location', {}).get('longitude', None),
                                    data_source = "https://deces.matchid.io",
                                    data_source_help_text = "",
                                    data_source_help_url = "https://deces.matchid.io/about"
                                )
                            ],
                            'birthdate': datetime.strptime(dead.get('birth', {}).get('date', ""), '%Y%m%d').strftime('%d/%m/%Y'),
                            'birthaddr': OpseAddress(
                                state_code = dead.get('birth', {}).get('location', {}).get('codePostal', ""),
                                city = dead.get('birth', {}).get('location', {}).get('city', ""),
                                country = dead.get('birth', {}).get('location', {}).get('country', ""),
                                data_source = "https://deces.matchid.io",
                                data_source_help_text = "",
                                data_source_help_url = "https://deces.matchid.io/about"
                            ),
                            'deathdate': datetime.strptime(dead.get('death', {}).get('date', ""), '%Y%m%d').strftime('%d/%m/%Y'),
                            'deathaddr': OpseAddress(
                                state_code = dead.get('death', {}).get('location', {}).get('codePostal', ""),
                                city = dead.get('death', {}).get('location', {}).get('city', ""),
                                country = dead.get('death', {}).get('location', {}).get('country', ""),
                                data_source = "https://deces.matchid.io",
                                data_source_help_text = "",
                                data_source_help_url = "https://deces.matchid.io/about"
                            )
                        })

            else:
                print_warning("No person found for " + firstname.capitalize() + " " + lastname.capitalize())

        else:
            print_error(" An error occured while searching deads' data")
            return None

        # Return a list of Profiles
        return deads
