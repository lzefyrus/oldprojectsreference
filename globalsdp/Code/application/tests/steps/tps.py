from behave import *


@given('we have tps')
def step_impl(context):
    pass


@when('we implement a test tps')
def step_impl(context):
    assert True is not False


@then('behave will test tps for us!')
def step_impl(context):
    assert context.failed is False
