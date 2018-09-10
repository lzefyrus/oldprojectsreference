from behave import *


@given('we have utils')
def step_impl(context):
    pass


@when('we implement utils')
def step_impl(context):
    assert True is not False


@then('behave will test utils for us!')
def step_impl(context):
    assert context.failed is False
