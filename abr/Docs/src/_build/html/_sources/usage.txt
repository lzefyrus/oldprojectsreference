Usage
======

Ednpoint
--------

Main url for server: http://internal-lbi-abr-prod-589612350.sa-east-1.elb.amazonaws.com/<action>/?<phone>
 - action:
     - **doc**: shows documentation of the project
     - **search**: look up for a phone in the database; where phone must follow one of the patterns:
           - ?(+)?(DDI[2])(DDD[2])(PHONE[8-9])
           - ex1. +551150610339
           - ex2. 1150610339
           - ex3. 5511991910324

Return
------

Not ported phone:
^^^^^^^^^^^^^^^^^

::

    {
	9digit: true,
	dataInicio: "",
	dataPortabilidade: "",
	mobile: true,
	operadora: "tim",
	portado: false,
	provincia: "",
	telefone: "11930060999",
	uf: ""
	}

Ported phone:
^^^^^^^^^^^^^^^^^

::

    {
	9digit: true,
	dataInicio: "Sat, 30 May 2015 01:13:39 GMT",
	dataPortabilidade: "Wed, 04 Apr 2012 12:02:44 GMT",
	mobile: false,
	operadora: "tim",
	portado: true,
	provincia: "",
	telefone: "1199112343",
	uf: "sp"
	}

Errors:
^^^^^^^
Invalid searched phone

::
	{
	error: "invalid phone"
	}

Phone not found on database

::
	{
	error: "phone not found"
	}