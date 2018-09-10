from soapfish import soap, xsd


class GetUser(xsd.ComplexType):
    id = xsd.Element(xsd.String, minOccurs=1)


class User(xsd.ComplexType):
    INHERITANCE = None
    name = xsd.Element(xsd.String, minOccurs=0)
    cpf = xsd.Element(xsd.String, minOccurs=0)
    email = xsd.Element(xsd.String, minOccurs=0)
    mobile = xsd.Element(xsd.String, minOccurs=0)
    address = xsd.Element(xsd.String, minOccurs=0)
    cep = xsd.Element(xsd.String, minOccurs=0)
    city = xsd.Element(xsd.String, minOccurs=0)
    neighborhood = xsd.Element(xsd.String, minOccurs=0)
    numb = xsd.Element(xsd.String, minOccurs=0)

    @classmethod
    def create(cls, name, cpf, email, mobile, address, cep, city, neighborhood, numb):
        instance = cls()
        instance.name = name
        instance.cpf = cpf
        instance.email = email
        instance.mobile = mobile
        instance.address = address
        instance.cep = cep
        instance.city = city
        instance.neighborhood = neighborhood
        instance.numb = numb

        return instance


class StockPrice(xsd.ComplexType):
    nillable = xsd.Element(xsd.Int, nillable=True)
    prices = xsd.ListElement(xsd.Decimal(fractionDigits=2), tagname="price", minOccurs=0, maxOccurs=xsd.UNBOUNDED,
                             nillable=True)


class Users(xsd.ComplexType):
    INHERITANCE = None
    user = xsd.ListElement(User, tagname="users", minOccurs=0)


Schema = xsd.Schema(
    # Should be unique URL, can be any string.
    targetNamespace="http://next.me/user.xsd",
    # Register all complex types to schema.
    complexTypes=[Users, User, GetUser],
    elements={"getUser": xsd.Element(GetUser),
              "users": xsd.Element(Users),
              "user": xsd.Element(User)}
)


def get_user(request, user=None):
    fid = user.id
    users = Users()
    for i in range(0, 10):
        uu = User(
            name="Sandro - {}".format(i),
            city="São Paulo",
            email="sandro.lourenco@rga.com",
            mobile="11991504030",
            address="Rua xpto",
            cep="013312000",
            neighborhood="jd america",
            numb="11"
        )
        users.user.append(uu)
    # user.nnn = 'dasasd'
    return users


get_user_method = xsd.Method(
    function=get_user,
    soapAction="http://next.me/user/get_user",
    input="getUser",
    output="users",
    operationName="http://next.me/user")

SERVICE = soap.Service(
    name="NextUser",
    targetNamespace="http://next.me/user.wsdl",  # WSDL targetNamespce
    version=soap.SOAPVersion.SOAP11,
    # location="http://test-api.next.me:5000/user",
    location="http://127.0.0.1:5000/user",
    schemas=[Schema],
    methods=[get_user_method])
