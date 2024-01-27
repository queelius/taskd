import requests

def count_words_at_url(url):
    resp = requests.get(url)
    return len(resp.text.split())


# let's time it
import time
start = time.time()
count = count_words_at_url('https://metafunctor.com')
end = time.time()

print(f'Word count at https://metafunctor.com took {end - start} seconds')

# let's introduce 1 minute delay
print('Waiting 60 seconds...')
time.sleep(60)
print(f'Word count at https://metafunctor.com is: {count}')
