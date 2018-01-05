Feldman User's Guide
--------------------
*December 12, 2017*
*version 0.0.2*

TODO: Table of Contents

### File Formats
Feldman reads and writes tabular data files in comma-separated values (CSV) format.

General requirements:

*   The first row of a file must be a header row with a name for each column.
*	All subsequent rows must be data rows; no additional rows (e.g. units, comments) are allowed.
*   Names of columns required by a format must match exactly, they are case-sensitive.
*   One or more non-required columns are allowed if their names are unique.
*   Columns can be in any order.

#### Identity Columns

All formats must include the following identity columns:

>		Site: An integer > 0 representing the collection site  
>		Hole: One or more capital letters (A, B, ..., Y, Z, AA, AB...) representing a single drilled hole  
>		Core: An integer > 0 representing an interval of material collected from parent hole  
>		Tool: A single capital letter representing the drilling tool used to collect the core  


All formats, with the exception of affine and section summary tables, also include:
  
>		Section: An integer > 0 representing a subdivision of a core


#### Section Summary
A section summary table contains one row of data for every section in a project.
It is used to translate section depths to total depth, and as a "master list" of a
project's core sections. Sections that may not be included in a splice, but are part
of measurement data to be spliced should be included.

A section summary must include the following columns: 

>		Identity Columns, including Section: see above  
>		TopDepth: Top depth of the section, in meters (m)
>		BottomDepth: Bottom depth of the section, in meters (m)
>		TopDepthScaled: Scaled (in situ) top depth of the section, in meters (m) 
>		BottomDepth: Scaled (in situ) bottom depth of the section, in meters (m)
>		CuratedLength: Length of the curated section, in meters (m)

#### Affine
An affine table contains one row of data for every core in a project. Each row
includes the affine shift distance and associated metadata. 

#### Splice Interval
A splice interval table contains one row of data for each interval of a splice.

#### Sparse Splice
A sparse splice table contains one row of data for each interval of a sparse splice.
It is similar to a splice interval table, but each interval is defined only in section depths,
not total depths.

A sparse splice table must include the following columns:

>		Identity Columns, excluding Section: see above
>		Top Section: section in which the interval begins
>		Top Offset: section depth at which interval beings, in centimeters (cm)
>		Bottom Section: section in which the interval ends
>		Bottom Offset: section depth at which interval ends, in centimeters (cm)
>		Splice Type: TIE or APPEND
>		Data Used: Data type used to define this interval
>		Comment: Users' comments on interval
>		Gap (m): User-defined gap between current and preceding interval, in meters (m). Overrides default.

The Data Used, Comment, and Gap (m) column headers are required, but values in these columns are optional
and can be left empty. Non-empty values will be processed.


#### Manual Correlation
A manual correlation table contains one or more rows of data, each indicating a user-defined alignment
of an off-splice core with an on-splice core. The resulting affine shift will override the default affine
shift for the off-splice core. Each row consists of two sets of Identity Columns, and the point on each core to be aligned.

A manual correlation table must include the following columns:

>		Site1: The on-splice site
>		Hole1: The on-splice hole
>		Core1: The on-splice core
>		Tool1: The on-splice tool
>		Section1: The on-splice section
>		SectionDepth1: Section depth of the on-splice section to be aligned with off-splice section
>		Site2: The off-splice site  
>		Hole2: The off-splice hole
>		Core2: The off-splice core
>		Tool2: The off-splice tool
>		Section2: The off-splice section
>		SectionDepth2: Section depth of the off-splice section to be aligned with on-splice section


#### Measurement Data
A measurement data table contains one or more measurements taken at a given depth in a core section.

A measurement data table must include the following columns:

>		Identity Columns, including Section: see above
>		Depth: total depth of the measurement(s) of the core section, in meters (m).