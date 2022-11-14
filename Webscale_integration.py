# Disable insecure warnings
requests.packages.urlib3.disable_warnings()  # pylint: disable=no-member


''' CLIENT CLASS '''


class Client(BaseClient):
    def __init__(self, base_url: str, api_key: str):
        super().__init__(base_url=base_url)

        self.api_key = api_key

        if self.api_key:
            self._headers = {"Authorization": "Bearer {}".format(self.api_key)}

    def get_address_sets(self) -> Dict[str, Any]:
        """Returns all the address sets associated with the caller's account by sending a GET request

        Returns:
            Dict containing the address sets as returned from the API

        """

        return self._http_request(
            method='GET',
            url_suffix='/address-sets'
        )

    def get_address_set(self, id: str) -> Dict[str, Any]:
        """ Get the configuration of the specified address set by sending a GET request

        Args:
            id: The address set id. You can get the address set id's associated with the caller's account by running !webscale-address-sets

        Returns:
            Dict containing the address set config as returned from the API
        """

        return self._http_request(
            method='GET',
            url_suffix=f'/address-sets/{id}'
        )

    def get_address_set_members(self, id: str) -> Dict[str, Any]:
        """Get the IP addresses from the specified address set by sending a GET request

        Args:
            id: The address set id. You can get the address set id's associated with the caller's account by running !webscale-address-sets

        Returns:
            Dict containing the IP addresses as returned from the API
        """

        return self._http_request(
            method='GET',
            url_suffix=f'/address-sets/{id}/addresses'
        )

    def get_address_set_add_member(self, id: str, address: str, entries) -> Dict[str, Any]:
        """Add IP address to the specified address set by sending a PATCH request

        Args:
            id: The address set id. You can get the address set id's associated with the caller's account by running !webscale-address-sets
            address: The IP address to add to the address set

        Returns:
            Dict containing the IP addresses as returned from the API
        """

        return self._http_request(
            method='PATCH',
            url_suffix=f'/address-sets/{id}',
            json_data={"entries": entries}
        )



''' COMMAND FUNCTIONS '''


def test_module(client: Client) -> str:
    """Test API connectivity and authentication'

    Returning 'ok' indicates that the integration works like it is supposed to.
    Connection to the service is successful.
    Raises exceptions if something goes wrong.
    """

    # INTEGRATION DEVELOPER TIP
    # Client class should raise the exceptions, but if the test fails
    # the exception text is printed to the Cortex XSOAR UI.
    # If you have some specific errors you want to capture (i.e. auth failure)
    # you should catch the exception here and return a string with a more
    # readable output (for example return 'Authentication Error, API Key
    # invalid').
    # Cortex XSOAR will print everything you return different than 'ok' as
    # an error
    try:
        client.get_address_sets()

    except Exception as e:
        exception_text = str(e).lower()
        if 'forbidden' in exception_text or 'authorization' in exception_text:
            return 'Authorization Error: make sure API Key is correctly set'
        else:
            raise e
    return 'ok'


def get_address_sets_command(client: Client) -> CommandResults:
    response = client.get_address_sets()

    readable_output = tableToMarkdown('Address Sets', response)

    return CommandResults(outputs_prefix='Webscale Address Sets',
                          raw_response=response,
                          readable_output=readable_output
                          )

    
def get_address_set_command(client: Client, id: str) -> CommandResults:
    response = client.get_address_set(id)

    readable_output = tableToMarkdown('Address Set Config', response)

    return CommandResults(outputs_prefix='Webscale Address Set',
                          raw_response=response,
                          readable_output=readable_output
                          )
    

def get_address_set_members_command(client: Client, id: str, address: str) -> CommandResults:
    response = client.get_address_set_member(id)

    readable_output = tableToMarkdown('IP Addressesin Address Set', response)

    readable CommandResults(outputs_prefix='Webscale Address Set IP Addresses',
                            raw_response=response,
                            readable_output=readable_output
                            )
    

def get_address_set_is_member_command(client: Client, id: str, address: str) -> bool:
    response = client.get_address_set_members(id)
    is_member = False

    for item in response:
        if item['address'] == address:
            is_member = True

    return is_member
    

def get_address_set_is_blocked_command(client: Client, id: str, address: str) -> bool:

    return get_address_set_is_member_command(client, id, address)

    
def get_address_set_is_throttled_command(client: Client, id: str, address: str) -> bool:

    return get_address_set_is_member_command(client, id, address)


def get_address_set_add_member_command(client: Client, id: str, address: str) -> CommandResults:
    if get_address_set_is_member_command(client, id, address) == False:

        entries = client.get_address_set_members(id)

        entry=(
            "address": f"(address)",
            "description": "Added by Cortex XSOAR"
        )

        entries.append(entry)

        response = client.get_address_set_add_member(id, address, entries)

        readable_output = tableToMarkdown('Address Set Config', response)

        return CommandResults(outputs_prefix='Webscale Address Set',
                              raw_response=response,
                              readable_output=readable_output
                              )

    else:
        print(f"IP address {address} is already a member of address set {id}")
        return get_address_set_members_command(client, id)


''' MAIN FUNCTION '''


def main() -> None:
    """main function, parses params and runs command functions

    Returns:
        Returns the results to the War Room
    
    """
    params = demisto.params()
    args = demisto.args()
    command = demisto.command()

    api_key = params.get('apikey', {}).get('password')

    # get the service API url
    base_url = params.get('url')

    # INTEGRATION DEVELOPER TIP
    # You can use functions such as ``demisto.debug()``, ``demisto.info()``,
    # etc. to print information in the XSOAR server log. You can set the log
    # level on the server configuration
    # See: https://xsoar.pan.dev/docs/integrations/code-conventions#logging

    demisto.debug(f'Command being called is {command}')
    try:
        client = Client(base_url=base_url,
                        api_key=api_key)

        if command == 'test-module':
            # This is the call made when pressing the integration Test button.
            return_results(test_module(client))

        elif command == 'webscale-address-sets':
            return_results(get_address_sets_command(client))

        elif command == 'webscale-address-set':
            return_results(get_address_set_command(client, **args))

        elif command == 'webscale-address-set-members':
            return_results(get_address_set_members_command(client, **args))

        elif command == 'webscale-address-set-is-member':
            return_results(get_address_set_is_member_command(client, **args))

        elif command == 'webscale-address-set-is-blocked':
            return_results(get_address_set_is_blocked_command(client, **args))

        elif command == 'webscale-address-set-is-throttled':
            return_results(get_address_set_is_throttled_command(client, **args))

        elif command == 'webscale-address-set-add-member':
            return_results(get_address_set_add_member_command(client, **args))

        else:
            raise NotImplementedError(f"command {command} is not implemented.")

    # Log exceptions and return errors
    except Exception as e:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error("\n".join(("Failed to execute {command} command.", "Error:", str(s))))


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()

