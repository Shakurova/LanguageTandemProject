import argparse
import pandas as pd


# The templates should contain  [name] [match_speak] [match_learn] [match_name] [match_email]
full_match_message = open('./templates/full_match_message.txt', 'r').read().replace('\n', ' ')
partial_match_with_advanced_message = open('./templates/partial_match_with_advanced_message.txt', 'r').read().replace('\n', ' ')
partial_match_with_native_message = open('./templates/partial_match_with_native_message.txt', 'r').read().replace('\n', ' ')
no_match_message = open('./templates/no_match_message.txt', 'r').read().replace('\n', ' ')


def count_possible_matches(responses):
    """ Counting possible matches (needed for sorting)... """
    possible_matches = {}
    for index_person, row_person in responses.iterrows():
        person_info = _get_data(row_person)
        possible_matches[person_info['name']] = 0
        for index_matches, row_matches in responses.iterrows():
            match_info = _get_data(row_matches)
            if index_person != index_matches:
                if _full_match(person_info, match_info)[0] or _partial_match(person_info, match_info)[0] or _partial_match(match_info, person_info)[0]:
                    possible_matches[person_info['name']] += 1
    return possible_matches

def _get_data(row):
    """ Return dictionary with participant's data. """
    info = {}
    info['name'] = row['name']
    info['languages_to_practice'] = set(row['language_to_practice'].split(', '))
    info['native'] = set(row['native'].split(', '))
    info['advanced'] = set(row['advanced'].split(', ')) if type(row['advanced']) == str else set()
    info['only_native'] = row['only_native']
    info['email'] = row['email']
    info['facebook'] = row['facebook']
    return info

def _full_match(person_info, match_info):
    """ When both of the partners offer their native language. """
    match_speak = person_info['languages_to_practice'] & match_info['native']
    match_learn = person_info['native'] & match_info['languages_to_practice']
    return match_speak != set() and match_learn != set(), match_speak, match_learn

def _partial_match(person_info, match_info):
    """ When one of tha partners offers advanced language and another one - native. """
    match_speak = match_info['native'] & person_info['languages_to_practice']
    match_learn = person_info['advanced'] & match_info['languages_to_practice']
    return match_speak != set() and match_learn != set() and match_info['only_native'] == 'No', match_speak, match_learn


def create_matches(responses, possible_matches_dict):
    """ Return dictionary with the information about match and save the match_type. """
    done = []
    matches = {}
    for name in sorted(possible_matches_dict, key=possible_matches_dict.get, reverse=False):
        if name not in done:
            print(name, possible_matches_dict[name])
            person_info = _get_data(responses[responses['name'] == name].iloc[0])
            for index_matches, row_matches in responses.iterrows():
                match_info = _get_data(row_matches)
                if row_matches['name'] not in done:
                    if _full_match(person_info, match_info)[0]:
                        matches = _save_match(matches, person_info, match_info, _full_match(person_info, match_info), match_type='full_match')
                        done.append(name)
                        done.append(row_matches['name'])
                        break
                    elif _partial_match(person_info, match_info)[0]:
                        matches = _save_match(matches, person_info, match_info, _partial_match(person_info, match_info), match_type='partial_match', prefix=True)
                        done.append(name)
                        done.append(row_matches['name'])
                        break
                    elif _partial_match(match_info, person_info)[0]:
                        matches = _save_match(matches, person_info, match_info, _partial_match(match_info, person_info), match_type='partial_match', prefix=True)
                        done.append(name)
                        done.append(row_matches['name'])
    print(matches)
    return matches

def _save_match(matches, person_info, match_info, matching_languages, match_type, prefix=False):
    """ Return dictionary with the information about match. """
    person_name = person_info['name']
    match_name = match_info['name']
    matches[person_name] = {}
    matches[match_name] = {}

    matches[person_name]['match_name'] = match_info['name']
    matches[person_name]['match_type'] = match_type
    if prefix:
        matches[person_name]['match_type'] = matches[person_name]['match_type'] + '_with_native'
    matches[person_name]['match_email'] = match_info['email']
    matches[person_name]['match_facebook'] = match_info['facebook']
    matches[person_name]['match_speak'] = matching_languages[1]
    matches[person_name]['match_learn'] = matching_languages[2]

    matches[match_name]['match_name'] = person_info['name']
    matches[match_name]['match_type'] = match_type
    if prefix:
        matches[match_name]['match_type'] = matches[match_name]['match_type'] + '_with_advanced'
    matches[match_name]['match_email'] = person_info['email']
    matches[match_name]['match_facebook'] = person_info['facebook']
    matches[match_name]['match_speak'] = matching_languages[2]
    matches[match_name]['match_learn'] = matching_languages[1]

    return matches


def write_email(row_person, responses, matches):
    if row_person['match_name'] != 'Pair not found':
        if matches[row_person['name']]['match_type'] == 'full_match':
            message = _fill_email(full_match_message, row_person['name'], matches[row_person['name']])
        elif matches[row_person['name']]['match_type'] == 'partial_match_with_advanced':
            message = _fill_email(partial_match_with_advanced_message, row_person['name'], matches[row_person['name']])
        elif matches[row_person['name']]['match_type'] == 'partial_match_with_native':
            message = _fill_email(partial_match_with_native_message, row_person['name'], matches[row_person['name']])
    else:
        message = no_match_message.replace('[name]', row_person['name'])

    return message

def _fill_email(email_template, name, matches):
    """ Replace placefolders in email template with personal data. """
    match_name = str(matches['match_name'])
    match_email = str(matches['match_email'])
    match_facebook = str(matches['match_facebook'])
    match_speak = str(', '.join(matches['match_speak']))
    match_learn = str(', '.join(matches['match_learn']))

    message = email_template.replace('[name]', name)
    message = message.replace('[match_name]', match_name)
    message = message.replace('[match_email]', match_email)
    message = message.replace('[match_speak]', match_speak)
    message = message.replace('[match_learn]', match_learn)

    return message


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create language exchange partners matches.')
    parser.add_argument('--input_file', type=str, default='./responses/responses_2019.csv', help='Input file with the responses')
    parser.add_argument('--output_file', type=str, default='./results/matches_2019.v1.csv', help='Output file with the matches')
    args = parser.parse_args()

    # Read responses into a DafaFrame
    responses = pd.read_csv(args.input_file, delimiter=',')
    def get_name(row):
        return row['first'] + ' ' + row['second']
    responses['name'] = responses.apply(get_name, axis=1)

    # Count possible matches
    possible_matches_dict = count_possible_matches(responses)

    # Generate matches
    matches = create_matches(responses, possible_matches_dict)

    # Save matching info
    def get_match_name(row):
        if row['name'] in matches:
            return matches[row['name']]['match_name']
        else:
            return 'Pair not found'

    def get_match_type(row):
        if row['name'] in matches:
            return matches[row['name']]['match_type']
        else:
            return 'no_match'

    def get_options(row):
        return possible_matches_dict[row['name']]

    responses['match_name'] = responses.apply(get_match_name, axis=1)
    responses['match_type'] = responses.apply(get_match_type, axis=1)
    responses['options'] = responses.apply(get_options, axis=1)

    # Create an email and save the matches
    responses['message'] = responses.apply(write_email, axis=1, responses=responses, matches=matches)
    responses.to_csv(args.output_file)
