def call_deepseek_skill(client, params):
    return client.generate_prompt(**params)


def call_style_review_skill(client, params):
    return client.review_style(**params)
