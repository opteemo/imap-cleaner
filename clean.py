import sys
import json
import imaplib
import ssl
import os.path
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr


def read_args():
    configuration_file = sys.argv[1] if len(sys.argv) >= 2 else None
    delete_file = sys.argv[2] if len(sys.argv) >= 3 else None
    return configuration_file, delete_file


def print_usage():
    print(sys.argv[0], "<configuration file> <delete file>")


def read_configuration_file(path):
    with open(path, 'r') as configuration_file:
        config = json.load(configuration_file)
        return config


def read_delete_file(path):
    delete_list = []

    if path:
        with open(path, 'r') as delete_file:
            for line in delete_file.readlines():
                line = line.strip()
                if len(line) > 0 and line[0] != '#':
                    delete_list.append(line)

    return delete_list


def open_imap(config):
    if config["ssl"]:
        ssl.create_default_context()
        server = imaplib.IMAP4_SSL(config["host"], config["port"])
    else:
        server = imaplib.IMAP4(config["host"], config["port"])

    server.login(config["user"], config["password"])
    return server


def close_imap(server):
    server.expunge()
    server.close()
    server.logout()


def normalize_email_address(email_address):
    email_address = email_address.replace("\\r", "")
    email_address = email_address.replace("\\n", "")
    email_address = email_address.replace("\\", "")
    email_address = email_address.replace("'", "")
    email_address = email_address.replace('"', '')
    email_address = email_address.lower()
    return email_address


def delete_emails(server, delete_list):
    typ, msgnums = server.select("INBOX")

    for num in range(1, int(msgnums[0])+1):
        status = "\033[32mKEEP  \033[0m"
        typ, data = server.fetch(str(num), 'BODY.PEEK[HEADER.FIELDS (FROM)]')

        realname, email_address = parseaddr(str(data[0][1]))
        email_address = normalize_email_address(email_address)

        for motif in delete_list:
            if motif in email_address:
                status = "\033[31mDELETE\033[0m"
                server.store(str(num), '+X-GM-LABELS', '\\Trash')
                #server.store(str(num), '+FLAGS', '\\Deleted')

        print(status, email_address)


def main():
    # Read command line arguments
    configuration_file, delete_file = read_args()
    if configuration_file is None:
        print_usage()
        sys.exit(2)

    # Read configuration files
    config = read_configuration_file(configuration_file)
    delete_list = read_delete_file(delete_file)

    # Delete emails
    server = open_imap(config)
    delete_emails(server, delete_list)
    close_imap(server)


if __name__ == "__main__":
    main()
