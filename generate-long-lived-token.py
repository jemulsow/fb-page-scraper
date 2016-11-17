import argparse
import requests
from ConfigParser import SafeConfigParser

import consts


def get_long_lived_token(secrets):
    """
    Makes an https request to Facebook to generate a long lived user token
    :param secrets: dict of secret params required
    :return: long lived user token string
    """
    params = {consts.CLIENT_ID: secrets[consts.APP_ID],
              consts.CLIENT_SECRET: secrets[consts.APP_SECRET],
              consts.GRANT_TYPE: consts.GRANT_TYPE_NAME,
              consts.GRANT_TYPE_NAME: secrets[consts.USER_TOKEN]}
    r = requests.get('https://graph.facebook.com/oauth/access_token',
                     params=params)
    if r.status_code != 200:
        print ("ERROR: Facebook API returned with error {}: {}".format(
                   r.status_code, r.text))
        exit(1)
    return r.text.split('=')[1].split('&')[0]


def parse_config():
    """
    Parses a config file for the needed secrets. Can be overridden
    by passing these values in as arguments when running this script.
    :return: dict with secrets
    """
    secrets = {consts.APP_ID: None,
               consts.APP_SECRET: None,
               consts.USER_TOKEN: None}
    config = SafeConfigParser()
    config.read(consts.CONFIG_FILE)

    # APP_ID
    try:
        secrets[consts.APP_ID] = config.get(consts.SECRETS_SECTION,
                                            consts.APP_ID)
    except:
        pass
    return secrets


def parse_args(secrets):
    """
    Defines and parses CLI args
    :param secrets: secrets from config file to use as defaults
    :return: args object of parsed args
    """
    cli_description = ("Takes a Facebook APP ID, Facebook APP Secret and a "
                       "Facebook generated short lived User Token. Generates "
                       "a Facebook long lived User Token with a 60 day "
                       "expiration. If any of these arguments are not passed "
                       "in, this script will look for them in "
                       "{}.".format(consts.CONFIG_FILE))
    parser = argparse.ArgumentParser(prog='generate-long-lived-token',
                                     description=cli_description)
    parser.add_argument('-i', '--app_id', required=False,
                        help="Facebook APP ID",
                        default=secrets[consts.APP_ID])
    parser.add_argument('-s', '--app_secret', required=False,
                        help="Facebook APP Secret",
                        default=secrets[consts.APP_SECRET])
    msg = ("Facebook Short-lived User Token. Generate one here: "
           "https://developers.facebook.com/tools/explorer")
    parser.add_argument('-t', '--user_token', required=False,
                        help=msg,
                        default=secrets[consts.USER_TOKEN])
    msg = ("Store the generated long-lived token as {} in {}.".format(
               consts.USER_TOKEN_LL, consts.CONFIG_FILE))
    parser.add_argument('-w', '--write', required=False,
                        action='store_true', help=msg)
    return parser.parse_args()


def store_token(token):
    """
    Stores a token string in the config file
    :param token: token string to store
    :return:
    """
    config = SafeConfigParser()
    config.read(consts.CONFIG_FILE)
    sections = config.sections()
    if consts.SECRETS_SECTION not in sections:
        config.add_section(consts.SECRETS_SECTION)
    config.set(consts.SECRETS_SECTION, consts.USER_TOKEN_LL, token)

    try:
        with open(consts.CONFIG_FILE, 'w') as f:
            config.write(f)
    # TODO: work out permission issues
    except Exception as e:
        print ("ERROR: Error writing token to config file {}. "
               "{}".format(consts.CONFIG_FILE, e))
        exit(1)


def main():
    # Parse config options
    secrets = parse_config()
    # Parse args from the command line
    args = vars(parse_args(secrets))

    for k, v in args.iteritems():
        if v is None:
            print ("ERROR: {} is required. Pass it in, or add it to "
                   "{}.".format(k, consts.CONFIG_FILE))
            exit(1)

    token = get_long_lived_token(args)
    print "Generated Long-lived User Token: {}".format(token)

    if args.get('write'):
        print "Storing long-lived token in {}".format(consts.CONFIG_FILE)
        store_token(token)

if __name__ == "__main__":
    main()
