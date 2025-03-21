## Assumptions that are different in Harmony

* We can't use short name and version with Harmony like we do with ECS, we have to use
  Concept ID (or DOI). We need to get this from CMR using short name and version.
* Differences in Harmony features
  * Variable subsetting won't be supported on day 1.
  * Reprojection and reformatting won't be supported on day 1.
* All the ICESat-2 products we currently support will not be supported on day 1.
    * <https://nsidc.atlassian.net/wiki/spaces/DAACSW/pages/222593028/ICESat-2+data+sets+and+versions+we+are+supporting+for+Harmony>
* Requests to CMR and ECS share parameters and are made through Python
  `requests`. Support for harmony will be implemented with `harmony-py` and
  `earthaccess` will be used for granule search and non-subset orders.


## Getting started on development

### Work so far

Work in progress is on the `harmony-take2` branch.


### OBE Work and "take2"

Matt Fisher began work on implementing support for Harmony in the `harmony`
branch. This depends on the `low-hanging-refactors` branch being merged. A PR is
open.

In addition to this work, refactoring, type checking, and type annotations have
been added to the codebase to support the migration to Harmony. Many of the
refactors ended up breaking large swaths of the code. The `harmony` branch is
OBE because we decided to take a different approach after further analysis.

The initial work assumed that icepyx would be directly making requests (via
e.g., the `requests` library) to the harmony API. Further development revealed
that [harmony-py](https://harmony-py.readthedocs.io/en/main/) should be used to
interact with the harmony API. Moreover, there is a growing realization that
[earthaccess](https://earthaccess.readthedocs.io/en/latest/) can simplify large
parts of icepyx as well.

As these developments began to be worked into the existing code, it became more
clear that more was being "broken" than added. Icepyx's code has a lot of
handling of various parameters to ensure that they are formatted correctly for
various APIs. Although this made sense when icepyx was first developed,
`harmony-py` and `earthaccess` can replace much of this code.

Instead of ripping out/refactoring large chunks of existing code in the `query`
and `granules` modules, "take2" (the `harmony-take2` branch) strives to
replicate existing functionality exposed by icepyx through the development of
new classes "from scratch".

E.g,. the `queryv2` module provides a `QueryV2` class that should replicate the
functionality of the `query.Query` class that is designed to interact with CMR
and the NSIDC EGI ordering system that is being decommissioned.

This approach lets the existing code and tests continue to work as expected
while parallel functionality is developed using `harmony-py` and
`earthaccess`. As this development progresses, tests can be migrated to use the
new class.


### Familiarize with Harmony

* Check out this amazing notebook provided by Amy Steiker and Patrick Quinn:
  <https://github.com/nasa/harmony/blob/main/docs/Harmony%20API%20introduction.ipynb>
* Review the interactive API documentation:
  <https://harmony.uat.earthdata.nasa.gov/docs/api/> (remember, remove UAT from URL if
  Harmony is live with ICESat-2 products in early October 2024)
* [harmony-py docs](https://harmony-py.readthedocs.io/en/main/)


### Watch out for broken assumptions

It's important to note that two major assumptions will require significant refactoring.
The type annotations will help with this process!

* Broken assumption: "We can query with only short_name and version number". Harmony
   requires a unique identifier (concept ID or DOI). E.g.:
   <https://harmony.uat.earthdata.nasa.gov/capabilities?collectionId=C1261703129-EEDTEST>
   (NOTE: UAT query using a collection from a test provider; we should be using
   `NSIDC_CUAT` provider in real UAT queries and `NSIDC_CPRD` for real prod queries).
   Since we want the user to be able to provide short_name and version, implementing the
   concept ID as a `@cached_property` on `Query` which asks CMR for the concept ID makes
   sense to me.
* Broken assumption: Harmony features are equivalent to NSIDC's ECS-based
  ordering system. As mentioned above, Harmony will not support variable
  subsetting, reprojection, or reformatting for IS2 collections on day 1. In the
  future, these features may be implemented in Harmony. For now, we need to
  update existing code and user documentation to remove references to these
  features.


### Don't forget to enhance along the way

* Now that we're ripping things apart and changing parameters, I think it's important to
  replace the TypedDict annotations we're using with Pydantic models. This will enable us
  to better encapsulate validation code that's currently spread around.


## Testing with Harmony


To run `QueryV2` specific tests (places real Harmony orders and waits for
results - this can take a while):


```
pytest icepyx/tests/integration/test_queryv2.py
```

> [!WARNING]
> I noticed that when running tests with `pytest`, sometimes I would get errors
> related to earthdata login. I see that `conftest.py` is setup to mock out some
> login credentials by editing the user's `.netrc`. This results in a broken
> `.netrc`. I'm not sure how this is intended to work, but I resorted to
> removing those bits from `conftest.py` to get things working consistently.

Be sure to run the type checker periodically as well:

```
pyright
```

Eventually, once the `QueryV2` class has the required features implemented, we
will plan to replace the existing `Query` class with it. Ideally we can migrate
other existing tests that are specific to the `Query` class to the new `QueryV2`
class at that time.


## Integrating with other ongoing Icepyx work

Harmony is a major breaking change, so we'll be releasing it in Icepyx v2.

We know the community wants to break the API in some other ways, so we want to include those in v2 as well!

Jessica is currently determining who can help work on these changes, and what that looks like. *If you, the
Harmony/ECS migration developer, identify opportunities to easily replace portions of Icepyx with _earthaccess_
or other libraries, take advantage of that opportunity.

## FAQ

### Which API?

Harmony has two APIs:

* [OGC Environmental Data Retrieval API](https://harmony.earthdata.nasa.gov/docs/edr-api)
* [OGC Coverages API](https://harmony.earthdata.nasa.gov/docs/api/)

Which should be used and when and why?


#### "Answer"

Use the [OGC Coverages API](https://harmony.earthdata.nasa.gov/docs/api/)!

> My take is that we ought to focus on the Coverages API for ICESat-2, since we aren’t
> making use of the new parameters. And this is what they primarily support. But I don’t
> have a good handle on whether we ought to pursue the EDR API at any point.
>
> - Amy Steiker

See this thread on EOSDIS Slack for more details:

<https://nsidc.slack.com/archives/CLC2SR1S6/p1716482829956969>


## Remaining tasks

Remaining tasks for "take2" development include:

* Implement support for full-granule orders via `earthaccess`
* Check user inputs against supported harmony services. E.g., see `is2ref`
  module.
* Review documentation and jupyter notebooks for outdated information
  * Remove references to "NSIDC" ordering service.
  * Remove references to variable subsetting (this is not currently supported in
    Harmony, but may be in the future. No definitive plans yet).
  * Update references to OBE concepts like `reqparams` and `subsetparams`.
  * Cleanup references to reprojection/reformatting without subsetting
    * E.g., the [subsetting
      notebook](https://icepyx.readthedocs.io/en/latest/example_notebooks/IS2_data_access2-subsetting.html)
    indicates that reformatting and reprojection are options.
* Migrate existing tests to use new query class and the harmony/earthaccess approach.
* Updates to support cloud access (e.g., see [these docs on how to access data via s3](https://icepyx.readthedocs.io/en/latest/example_notebooks/IS2_cloud_data_access.html))
  * Ideally the underlying code is updated to use `earthaccess`.
  * There might not be much that needs to be done here.
* Update
  [QUEST](https://icepyx.readthedocs.io/en/latest/example_notebooks/QUEST_argo_data_access.html)-related
  code to enable support for the new query class.
  * It looks like QUEST support is currently limited to [Argo](https://argo.ucsd.edu/about/) data.
* Support passing other subsetting kwargs to harmony-py
