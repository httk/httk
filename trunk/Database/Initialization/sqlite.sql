CREATE TABLE Property 
(
        PropertyId               INTEGER PRIMARY KEY,
	ComputationId            INTEGER,
	PropertyDataTable        TEXT
);

CREATE TABLE PropertyData_FormationEnergy_0K
(
   /* Property data specific to one type of property */
   PropertyId                    INTEGER,
   FormationEnergy               REAL
);

CREATE TABLE PropertyData_DOS_0K
(
   /* Another example of a property data; DOS is big, so it is not in
    * the database. Instead this refers back to computational data. 
    */
   PropertyId                    INTEGER,
   DataPath                      TEXT
   /* internal path to DOS data in the hdf data tree of the associated Computation */
);

CREATE TABLE Geometry
(
   /* Each row is generated from source crystal structures +
    * a best effort process to generate a unique representation
    * of the crystal structure independent of species assignment
    * and volume. This is what is meant by a 'Geometry'.
    */
   GeometryId                    INTEGER PRIMARY KEY,
   UniqueRepresentation          TEXT
   /* further columns describing an abstract crystal structure to be added here  */
);

CREATE TABLE SpeciesMap 
(
   SpeciesMapId                  INTEGER PRIMARY KEY,
   UniqueRepresentation          TEXT
   /* {SpeciesAssignment}  : one -> many table */
);

CREATE TABLE SpeciesAssignment
(
   SpeciesMapId                  INTEGER,
   Site                          INTEGER, /* corresponding to the GeometryId */
   Species                       INTEGER, /* atomic number */
   Occupacy			 REAL
);

CREATE TABLE Computation
(
    ComputationId                INTEGER PRIMARY KEY,
    ComputationDate    		 TEXT,
    AddedDate                    TEXT,
    GeometryId                   INTEGER,
    SpeciesMapId                 INTEGER,
    Volume                       REAL,
    CodeId                       INTEGER,
    Hash                         TEXT
    /* Hash value of manifest file that lists hashes of all relevant data of the computation */
    /* {Related},      : one->many table */
    /* {Tag}           : one->many table */
    /* {Signature}     : one->many table */
);

CREATE TABLE Signature
(
    /* Keeps track for every computation a list of signatures that marks ownership
     */
    SignatureId                  INTEGER PRIMARY KEY,
    ComputationId                INTEGER,
    SignatureData                TEXT, /* Signs the Hash in the Computation table */
    KeyId                        INTEGER
);

CREATE TABLE ComputationRelated
(
    ComputationId                INTEGER,
    RelatedToComputationId       INTEGER,
    SequenceNumber               INTEGER, /* sets the sequence of related runs */
    Relation                     TEXT /* e.g. "Relaxation step" */
);

CREATE TABLE ComputationTag
(
    ComputationId                INTEGER,
    TagName                      TEXT, /* e.g., "spin-polarized" */
    TagValue                     TEXT /* e.g., "true" */
);

CREATE TABLE Code
(
    CodeId                       INTEGER PRIMARY KEY,
    CodeName                     TEXT,
    Version                      TEXT, /* (e.g. "2.4.16.32-beta") */
    Reference                    TEXT /* (e.g. a link to the VASP website) */
);

CREATE TABLE SignatureKey
(
    /* Table to keep track of generated ssl keys to
     * make it possible to handle identification of
     * "owners" of calculations
     */
    KeyId			INTEGER PRIMARY KEY,
    Description                 TEXT, /* E.g. name of person, or project, etc. */
    KeyData             	TEXT
);

CREATE INDEX Geometry_UniqueRepresentation ON Geometry(UniqueRepresentation);

CREATE INDEX SpeciesAssignment_SpeciesMapId ON SpeciesAssignment(SpeciesMapId);
CREATE INDEX SpeciesAssignment_Species ON SpeciesAssignment(Species);

CREATE INDEX Computation_ComputationDate ON Computation(ComputationDate);
CREATE INDEX Computation_AddedDate ON Computation(AddedDate);
CREATE INDEX Computation_GeometryId ON Computation(GeometryId);
CREATE INDEX Computation_SpeciesMapId ON Computation(SpeciesMapId);
CREATE INDEX Computation_CodeId ON Computation(CodeId);

CREATE INDEX Signature_ComputationId ON Signature(ComputationId);
CREATE INDEX Signature_KeyId ON Signature(KeyId);

CREATE INDEX ComputationRelated_ComputationId ON ComputationRelated(ComputationId);
CREATE INDEX ComputationRelated_RelatedToComputationId ON ComputationRelated(RelatedToComputationId);

CREATE INDEX ComputationTag_ComputationId ON ComputationTag(ComputationId);
CREATE INDEX ComputationTag_TagName ON ComputationTag(TagName);
CREATE INDEX ComputationTag_TagValue ON ComputationTag(TagValue);

