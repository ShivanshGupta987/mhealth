--
-- PostgreSQL database dump
--

\restrict QhHVaWku6nqqevzSIwNRhooHmIwWTffgRkrRXzfvVUeFcJp326QG3NIKufHvBjV

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

-- Started on 2026-02-27 09:18:12

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 2 (class 3079 OID 16601)
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- TOC entry 5098 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- TOC entry 895 (class 1247 OID 32795)
-- Name: call_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.call_status_enum AS ENUM (
    'Call Scheduled',
    'failed',
    'busy',
    'no-answer',
    'Message Not Conveyed',
    'Message Conveyed But Not Processed',
    'Message Conveyed And Processed'
);


ALTER TYPE public.call_status_enum OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 221 (class 1259 OID 16401)
-- Name: Admins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Admins" (
    "Admin_Id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "Email" character varying(255),
    "Password" character varying(255)
);


ALTER TABLE public."Admins" OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 16481)
-- Name: Calls; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Calls" (
    "Call_Id" uuid NOT NULL,
    "Call_Sid" character varying(100),
    "Target_Id" uuid,
    "Model_Id" character varying(10),
    "Scheduled_Time" timestamp with time zone,
    "Started_Time" timestamp with time zone,
    "Emotion_Id" character varying(10),
    "Status" public.call_status_enum,
    "Duration" integer,
    "Recording_Url" character varying(512),
    "Analysis_Score" double precision
);


ALTER TABLE public."Calls" OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 16411)
-- Name: Emotions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Emotions" (
    "Emotion_Id" character varying(10) NOT NULL,
    "Emotion" character varying(20)
);


ALTER TABLE public."Emotions" OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16419)
-- Name: Error_Logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Error_Logs" (
    "Logs_Id" uuid NOT NULL,
    "Timestamp" timestamp with time zone,
    "Error_Type" character varying,
    "Error_Message" text
);


ALTER TABLE public."Error_Logs" OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16615)
-- Name: FlaggedTargets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."FlaggedTargets" (
    "Flag_Id" uuid NOT NULL,
    "Target_Id" uuid NOT NULL,
    "Call_Scheduled_DateTime" timestamp with time zone
);


ALTER TABLE public."FlaggedTargets" OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 16427)
-- Name: Models; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Models" (
    "Model_Id" character varying(10) NOT NULL,
    "Model_Name" character varying,
    "Model_Version" character varying,
    "Model_Details" text
);


ALTER TABLE public."Models" OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 40964)
-- Name: Password_Reset_Tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Password_Reset_Tokens" (
    "Token_Id" uuid NOT NULL,
    "Admin_Id" uuid NOT NULL,
    "Token" character varying(255) NOT NULL,
    "Created_At" timestamp with time zone,
    "Expires_At" timestamp with time zone NOT NULL,
    "Used" integer
);


ALTER TABLE public."Password_Reset_Tokens" OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16459)
-- Name: Targets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Targets" (
    "Target_Id" uuid NOT NULL,
    "Name" character varying NOT NULL,
    "Department_Name" character varying NOT NULL,
    "Program" character varying NOT NULL,
    "Roll_No" character varying NOT NULL,
    "Phone_No" character varying
);


ALTER TABLE public."Targets" OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16395)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- TOC entry 5085 (class 0 OID 16401)
-- Dependencies: 221
-- Data for Name: Admins; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Admins" ("Admin_Id", "Email", "Password") FROM stdin;
83686ba9-745b-400e-8ef9-49dd025ec658	m.health@iitgn.ac.in	$bcrypt-sha256$v=2,t=2b,r=12$hvu.uJVUkwCGb0v3bgge0u$B5JeOtsdVg02kKmC2wY5pzv/Nrb0.by
\.


--
-- TOC entry 5090 (class 0 OID 16481)
-- Dependencies: 226
-- Data for Name: Calls; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Calls" ("Call_Id", "Call_Sid", "Target_Id", "Model_Id", "Scheduled_Time", "Started_Time", "Emotion_Id", "Status", "Duration", "Recording_Url", "Analysis_Score") FROM stdin;
ad1f8682-c6c9-4709-9c5a-3a1d5c07d14b	a76f47a02fc803c5aecb5043caf119cu	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-30 00:14:20.20571+05:30	2025-12-30 00:14:20.663505+05:30	\N	no-answer	\N	\N	\N
b8aec10f-9507-4910-b612-4f04f4f3320e	30c99e89990a7b20eaac9e8f2e8719cs	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-28 03:08:27.997191+05:30	2025-12-28 03:08:28.080505+05:30	\N	Message Conveyed But Not Processed	180	\N	\N
eb59fefa-9730-4d93-a774-87ca2d43eacd	492e56a8d148bb73e5999240b52219cu	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-30 00:18:33.255797+05:30	2025-12-30 00:18:33.410132+05:30	\N	no-answer	\N	\N	\N
b307977c-cb70-4376-b40c-ccfa3f6f4bee	bc9621df9b7c53645775f383ded919cu	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-30 00:21:41.562178+05:30	2025-12-30 00:21:41.66928+05:30	\N	busy	\N	\N	\N
f78edbe9-a9d3-42cc-99ab-b32b82814956	c8962b870cc340004a2f846a3de819cs	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-28 02:09:35.702521+05:30	2025-12-28 02:09:36.040912+05:30	\N	failed	0	\N	\N
e95f2a5d-85e1-4362-bbeb-90c774db12f7	1465dcf819b437550030ac223d6719cs	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-28 02:18:06.108888+05:30	2025-12-28 02:18:06.223834+05:30	\N	Call Scheduled	0	\N	\N
81bb6634-b275-4e6d-8713-b6fd00afe82d	fb6c29a38d19873912f6a268fbd319ct	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-29 03:25:54.43145+05:30	2025-12-29 03:25:54.59229+05:30	\N	Message Not Conveyed	25	\N	\N
b3e48094-4afc-4caa-a560-8b94ff4b5aa3	c6d0814b7a79d02e08d2e3a11cf319ct	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-29 03:13:38.470373+05:30	2025-12-29 03:13:38.582298+05:30	\N	Message Not Conveyed	22	\N	\N
fb4f9423-1a88-4551-a661-3e78b2e88f85	8c784f1439dcb7930544685d027519ct	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-29 01:51:45.318809+05:30	2025-12-29 01:51:45.588753+05:30	\N	Message Not Conveyed	29	\N	\N
258ed7bd-8d8e-4fa5-984a-eb0dbba43b9c	83f91d5b56160769a3d12596a2b119cs	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-28 14:57:24.442942+05:30	2025-12-28 14:57:24.663416+05:30	\N	Message Not Conveyed	19	http://localhost:9000/recordings/83f91d5b56160769a3d12596a2b119cs.mp3	\N
fc79db71-4581-4627-a5fe-850c0d151279	c4baaf68079c91f9c06b9016b5e419cs	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-28 03:07:03.879922+05:30	2025-12-28 03:07:04.010526+05:30	\N	Message Not Conveyed	12	\N	\N
79f0f37b-1acb-46a1-a7d4-d1b6eb093c8a	c7a29e4d81f36b5a902c4d7e1b8f63ac	c6da7cd2-6aa5-4466-a007-b914f8d4f73c	M001	2026-01-24 00:16:20.20571+05:30	2026-01-24 00:16:20.78571+05:30	E003	Message Conveyed And Processed	180	\N	0.9
cece4c24-e0c8-4fd7-a80e-a5d81bc56368	8f3d91a7c2b4e65d9a1f07bc3e8421ad	f60c46db-5c8e-42d6-8d5e-388a99ffa943	M001	2026-01-30 00:12:34.20571+05:30	2026-01-30 00:12:34.806599+05:30	E003	Message Conveyed And Processed	180	\N	0.7
62e5ebbe-6248-45c2-90b9-83d96d3e3445	2a618b372ec263bc65189c24c70f19cu	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2025-12-30 02:06:00.518457+05:30	2025-12-30 02:06:00.733175+05:30	E001	Message Conveyed And Processed	180	\N	0.3
5d283e0b-8b4b-4c80-aff6-53862edc8693	c7a29e4d81f36b5a902c4d7e1b8f63ac	e471c565-30cd-434a-9601-ea25eb46bc11	M001	2026-01-24 00:16:20.20571+05:30	2026-01-24 00:16:20.78571+05:30	E003	Message Conveyed And Processed	180	\N	0.86
\.


--
-- TOC entry 5086 (class 0 OID 16411)
-- Dependencies: 222
-- Data for Name: Emotions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Emotions" ("Emotion_Id", "Emotion") FROM stdin;
E001	NEGATIVE
E003	POSITIVE
E002	NEUTRAL
\.


--
-- TOC entry 5087 (class 0 OID 16419)
-- Dependencies: 223
-- Data for Name: Error_Logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Error_Logs" ("Logs_Id", "Timestamp", "Error_Type", "Error_Message") FROM stdin;
5933dadf-73d0-4b12-b5c2-8719181d79f8	2025-11-03 23:17:28.260876+05:30	Call Initiation Error	Target=dc3887a5-a1ce-4a7a-8180-710a2132f4f5, CallID=f393d6ea-8ecb-44b7-8212-7b4ddc327718, Error=Expecting value: line 1 column 1 (char 0), CorrelationID=45f40d09-3ad0-4fe2-a2d6-91360a886c82
5dccace0-411c-4e52-be50-94284602394c	2025-12-03 00:35:22.301316+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=dd1d4160-586a-4d73-b467-cc83b01fff7c, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=2e2d8fd2-2fbd-4d52-9c2d-8a168da98f43
ad6c47a3-1e95-4e9e-97f9-90bd3ba9399c	2025-12-03 00:36:23.558733+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=dd1d4160-586a-4d73-b467-cc83b01fff7c, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=43e4e790-3901-4d3e-b1dc-a5f2adc2142b
ddd98f20-11be-4e5f-809c-62fd9ac97ae8	2025-12-03 00:37:25.398472+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=dd1d4160-586a-4d73-b467-cc83b01fff7c, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=c3990af0-44b2-4998-a4ae-1e10bf673e25
dc038eaf-8fba-4f6b-9fdf-08bcdbde466e	2025-12-03 00:38:26.496121+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=dd1d4160-586a-4d73-b467-cc83b01fff7c, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=cb1b7c8d-f9e7-402f-9460-69452a17de9e
bf4822fa-772e-4ce8-bde8-01b22d313e69	2025-12-03 00:43:14.239274+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=ae24ce58-bd26-4886-a1c3-7dc2172a8697, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=726e04b9-2b8b-42ca-ad2f-85b87a7673d5
3a64dde0-5f17-4f3f-8274-5676414d2370	2025-12-03 00:44:15.556629+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=ae24ce58-bd26-4886-a1c3-7dc2172a8697, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=f437a123-7087-4cd5-be53-05f43156eda5
73aa6ba7-df8f-4008-9ce9-8190888578cd	2025-12-03 00:45:16.704873+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=ae24ce58-bd26-4886-a1c3-7dc2172a8697, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=64699aee-b2de-4fea-a306-3bb12df953e5
855332bc-68c7-4b39-9579-e00be50a6ec1	2025-12-03 00:46:17.628557+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=ae24ce58-bd26-4886-a1c3-7dc2172a8697, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=9bf0fde2-d9b0-4d52-a473-bf15aa4cba10
2969573b-7d29-4639-bbfa-a8d32a96be27	2025-12-03 21:54:20.793691+05:30	Call Initiation Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=dfdf477f-19a4-4da8-a388-032b5d9275e8, Error='To', CorrelationID=3de22a5c-e891-4153-a7e5-c269aa3322ba
01546073-f903-4e3f-a359-77fbee82228c	2025-12-03 21:56:07.66327+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=7de39462-549b-4c64-9312-dc3817207e3a, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=b39860e1-2e3f-4413-9d6f-18610a0939c5
1a1b557d-589e-4fc1-bb1b-6319dd0de250	2025-12-03 21:57:09.063521+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=7de39462-549b-4c64-9312-dc3817207e3a, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=892394b9-602f-4cb5-930e-7f8ca94e0540
65dd6f62-21e8-4f93-9d9e-ad9ab1c2946d	2025-12-03 21:58:10.284734+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=7de39462-549b-4c64-9312-dc3817207e3a, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=9a0c119f-55a2-4617-a0b9-4b6e29f77a1c
f1d3720e-baf7-4f8b-bbca-e4d996dbb7ac	2025-12-03 21:59:11.822073+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=7de39462-549b-4c64-9312-dc3817207e3a, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=30fa74c0-5f40-49de-bef2-9132ae13a481
9bcf56ee-cbd3-4f9d-80e5-92e5f1be4065	2025-12-20 23:45:32.399442+05:30	Exotel API Error	Target=e2d9b9d1-c28c-4fe4-aa19-f8367aae689d, CallID=7697f0e1-cb71-43e9-95b3-b887fffe557a, Error=403 Client Error: Forbidden for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=df445df0-78ba-4bf2-ab8d-5d0a589f59fe
bb55dcda-3e75-4ab2-b957-324583a7988c	2025-12-20 23:46:36.154348+05:30	Exotel API Error	Target=e2d9b9d1-c28c-4fe4-aa19-f8367aae689d, CallID=7697f0e1-cb71-43e9-95b3-b887fffe557a, Error=403 Client Error: Forbidden for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=cfee9283-46cd-4926-869a-3dc5736ecd84
3003ca16-ad7f-43a4-8f37-b5edb1d4de78	2025-12-21 00:02:53.905217+05:30	Call Initiation Error	Target=e2d9b9d1-c28c-4fe4-aa19-f8367aae689d, CallID=7697f0e1-cb71-43e9-95b3-b887fffe557a, Error=('Connection aborted.', ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None)), CorrelationID=44998743-b0ca-44e4-ba8f-5ee627644a13
b810b1da-f550-4bb1-9ad8-61193d309289	2025-12-21 01:56:55.726149+05:30	Call Initiation Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=a8cc432f-b710-4c26-a996-4e8ecf6c1d2e, Error=Invalid JSON response from Exotel API: <?xml version="1.0" encoding="UTF-8"?>\n<TwilioResponse>\n <Call>\n  <Sid>1037b758436324dadc42454a181a19cl</Sid>\n  <ParentCallSid/>\n  <DateCreated>2025-12-21 01:56:55</DateCreated>\n  <DateUpdated>2025-12, CorrelationID=f52f96f9-853c-4aac-b50b-4a01ed7d44d0
3967880e-b085-4d8d-9089-80c0cf75be11	2025-12-26 13:36:45.321355+05:30	Exotel API Error	Target=3d6bd109-6078-477e-8a9c-54ecc4b6d130, CallID=8eca186f-6929-4981-92f0-4dcd18351c81, Error=403 Client Error: Forbidden for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=72de4f7c-193f-4245-85a3-f6b711722d2a
204fd7a7-e561-4ecb-b9e2-5541a1d3cdc1	2025-12-26 13:36:45.321355+05:30	Exotel API Error	Target=d86706cf-17bf-41d4-9261-84702426c685, CallID=d01903e3-a6eb-41e1-8bc2-40752412b6e6, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=5aedefd6-8a39-4bd4-bcc4-f138f72e41ec
667d9ea6-5346-4c4f-907a-edfedf0dd311	2025-12-26 13:36:45.320346+05:30	Exotel API Error	Target=bc74c40e-1e3b-4e66-ae88-dd707d28add4, CallID=f1931143-d2e8-44dd-8dd1-1c07f9d46b33, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=40201e76-a401-49f9-ae10-f4fb434be814
b624458a-d6c0-4653-911d-5dd249f72d9e	2025-12-26 13:36:45.322373+05:30	Exotel API Error	Target=1ecd196f-b293-4d68-a1bf-84ee8c769f8d, CallID=fa026619-9266-4899-86ec-e600874b0076, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=c22a165c-6fa6-428d-b5d3-a91bb6a7b81a
5f2bb65c-042d-4f6d-a807-53f779e10083	2025-12-26 13:36:47.798659+05:30	Exotel API Error	Target=543e37a6-78e7-4825-9ebc-561bef1a096c, CallID=87319e7d-cfb9-48d6-af00-4a0357f03500, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=22e0eb1a-c661-45c5-a3b0-099fd87671c9
a5c9ffd2-06e2-42ed-a755-4b6a56c19be6	2025-12-26 13:36:47.800885+05:30	Exotel API Error	Target=ae933b5e-d978-41af-a84c-318707568046, CallID=70da8d3e-c34d-42b9-bbf2-b2f217872439, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=03dd24dc-68a0-46b5-aa55-2ea91875fcd6
274b4b0c-94f4-4bb9-ac98-e4730c705476	2025-12-26 13:36:47.807224+05:30	Exotel API Error	Target=d7120049-e0ce-48fd-9ed6-4a2802af1c42, CallID=5202b8a0-7178-4d23-8293-baa6ca434c4a, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=58b601ce-96a4-451e-b68a-4044f5a64c44
9f9fdf0a-2bec-4f1d-8001-66c591d25749	2025-12-26 13:36:50.565733+05:30	Exotel API Error	Target=38091e53-1fc9-4ed8-aba9-7bf7dd84ebde, CallID=0e8c86e2-6187-469f-896f-1544ffd41881, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=82398f8d-be32-459a-a67f-de280baedb16
2bafea9b-967f-4301-93de-305949af48b0	2025-12-26 13:36:47.808242+05:30	Exotel API Error	Target=2dce29b3-9427-43db-b45d-c7f189061fb3, CallID=2af048ee-2476-4835-baa2-07e47f2efe11, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=ea7f4792-c033-481e-ac3e-1433bc83eada
61368fd1-e75b-4027-a6f9-ff79686bd54e	2025-12-26 13:36:50.565733+05:30	Exotel API Error	Target=55889035-11d3-4400-94a0-2ce02298336b, CallID=56a392be-6ff3-432e-89b0-66acc6a99809, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=311819da-394d-468e-acc4-1925a2991a43
a4635de5-88b7-4a2a-b9de-9100ae6ec69a	2025-12-26 13:36:50.565733+05:30	Exotel API Error	Target=3d6bd109-6078-477e-8a9c-54ecc4b6d130, CallID=eef88f62-1708-4124-8731-7f8497083c59, Error=403 Client Error: Forbidden for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=df8c2ea1-5583-469d-94a6-89a973ea7c0e
839604d5-3882-4ec4-9342-ebf6582edbaa	2025-12-26 13:36:50.565733+05:30	Exotel API Error	Target=6987a34c-00ca-48f8-be7e-c5a496413024, CallID=0c68e090-b91b-4f83-ad92-75584ad07621, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=bc42a2b1-3a31-483a-8e0d-9e51e2a0543e
daac81eb-6000-489f-8842-8666c9c2f3c2	2025-12-26 13:45:06.112184+05:30	Exotel API Error	Target=1ecd196f-b293-4d68-a1bf-84ee8c769f8d, CallID=fa026619-9266-4899-86ec-e600874b0076, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=6f457eed-5dc2-427c-83e2-7a3e7ae1cb0d
67738c4a-cd11-4059-82b8-69b45a3c0cc4	2025-12-26 13:45:06.115174+05:30	Exotel API Error	Target=bc74c40e-1e3b-4e66-ae88-dd707d28add4, CallID=f1931143-d2e8-44dd-8dd1-1c07f9d46b33, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=ddfe1df7-963d-4f31-b2ee-889fa6416084
e827604c-2b9f-4c0a-98d5-6f1d18a5412f	2025-12-26 13:45:06.115174+05:30	Exotel API Error	Target=3d6bd109-6078-477e-8a9c-54ecc4b6d130, CallID=8eca186f-6929-4981-92f0-4dcd18351c81, Error=403 Client Error: Forbidden for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=9c0b50c1-f712-467e-9edb-d00f7faf5e46
efcc5c0c-b1a7-4deb-b783-9732b4c4090c	2025-12-26 13:45:06.115174+05:30	Exotel API Error	Target=d86706cf-17bf-41d4-9261-84702426c685, CallID=d01903e3-a6eb-41e1-8bc2-40752412b6e6, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=1dd10b56-f04c-4e06-bf54-a252c2bb3643
2747da4c-ee0b-452b-814c-b75b046aaf4a	2025-12-26 13:45:09.418701+05:30	Exotel API Error	Target=ae933b5e-d978-41af-a84c-318707568046, CallID=70da8d3e-c34d-42b9-bbf2-b2f217872439, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=a62c952b-6819-4553-a884-721b857432ff
8b6ef66c-d9c2-4097-a5d2-ba3eec3567bc	2025-12-26 13:45:09.421813+05:30	Exotel API Error	Target=2dce29b3-9427-43db-b45d-c7f189061fb3, CallID=2af048ee-2476-4835-baa2-07e47f2efe11, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=c565959a-d775-453f-9271-0f5a7e417682
38cb6193-3403-436f-8b8e-2518159dd371	2025-12-26 13:45:09.430351+05:30	Exotel API Error	Target=543e37a6-78e7-4825-9ebc-561bef1a096c, CallID=87319e7d-cfb9-48d6-af00-4a0357f03500, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=b631d2b7-e4d8-4606-aa2c-a96252020a13
38b7ce9b-90e7-47a6-9ed3-56894132ec80	2025-12-26 13:45:09.43368+05:30	Exotel API Error	Target=d7120049-e0ce-48fd-9ed6-4a2802af1c42, CallID=5202b8a0-7178-4d23-8293-baa6ca434c4a, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=dfcd1aee-7f96-4a94-ab78-566b1bd9199a
d00daa09-bbe6-49e1-9acf-ece14fe33a08	2025-12-26 13:45:12.819107+05:30	Exotel API Error	Target=38091e53-1fc9-4ed8-aba9-7bf7dd84ebde, CallID=0e8c86e2-6187-469f-896f-1544ffd41881, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=37fb9c40-3b59-42be-b10c-34ded5f9dd1b
26da7f73-be89-431b-9a09-ad184443690a	2025-12-26 13:45:12.843379+05:30	Exotel API Error	Target=3d6bd109-6078-477e-8a9c-54ecc4b6d130, CallID=eef88f62-1708-4124-8731-7f8497083c59, Error=403 Client Error: Forbidden for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=5635ba0f-0435-4df1-96c7-35ee9b1f3edf
0bbc9198-271b-4216-9a92-16d514a3fa27	2025-12-26 13:45:12.843379+05:30	Exotel API Error	Target=55889035-11d3-4400-94a0-2ce02298336b, CallID=56a392be-6ff3-432e-89b0-66acc6a99809, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=44f10d77-48c7-4ec2-b007-48d71ba0305a
37453682-ce17-4a9b-bfce-942276e537b7	2025-12-26 13:45:12.843379+05:30	Exotel API Error	Target=6987a34c-00ca-48f8-be7e-c5a496413024, CallID=0c68e090-b91b-4f83-ad92-75584ad07621, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=a2dcb213-3424-47fe-b3d3-e477fa96cea7
10a3f631-7416-416a-82c8-e1ac5abbfe6b	2025-12-26 13:46:16.199096+05:30	Exotel API Error	Target=1ecd196f-b293-4d68-a1bf-84ee8c769f8d, CallID=fa026619-9266-4899-86ec-e600874b0076, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=dd86ac32-0d03-4043-bcb1-d0b7929df0eb
e6b166cb-1d21-4541-8172-170737313c51	2025-12-26 13:46:16.200356+05:30	Exotel API Error	Target=bc74c40e-1e3b-4e66-ae88-dd707d28add4, CallID=f1931143-d2e8-44dd-8dd1-1c07f9d46b33, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=004cb980-cc91-43b5-8b46-b431663f07c7
a4bbf7c2-9943-45cd-b220-b65b3e7c3d5e	2025-12-26 13:46:16.200889+05:30	Exotel API Error	Target=d86706cf-17bf-41d4-9261-84702426c685, CallID=d01903e3-a6eb-41e1-8bc2-40752412b6e6, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=96e27ce2-1b5a-46ce-addc-8fb240e98e1f
9ac866d7-f691-4964-a614-6dcccfaa2e63	2025-12-26 13:46:16.201424+05:30	Exotel API Error	Target=3d6bd109-6078-477e-8a9c-54ecc4b6d130, CallID=8eca186f-6929-4981-92f0-4dcd18351c81, Error=403 Client Error: Forbidden for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=032b561b-55a0-4e2a-8150-f087047013d7
f27363a7-bc6a-4a8f-9c17-6f01523f970b	2025-12-26 13:46:18.918173+05:30	Exotel API Error	Target=d7120049-e0ce-48fd-9ed6-4a2802af1c42, CallID=5202b8a0-7178-4d23-8293-baa6ca434c4a, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=fb7156b7-9566-48c8-a3f7-80075d6b92df
6207cafd-6bb5-4871-99d1-7e7cd77faccd	2025-12-26 13:46:18.918173+05:30	Exotel API Error	Target=543e37a6-78e7-4825-9ebc-561bef1a096c, CallID=87319e7d-cfb9-48d6-af00-4a0357f03500, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=d0f22fed-62dc-429d-a811-99987f07f090
0958caa0-d7ec-49f4-a281-6298d50e4dc4	2025-12-26 13:46:18.922543+05:30	Exotel API Error	Target=2dce29b3-9427-43db-b45d-c7f189061fb3, CallID=2af048ee-2476-4835-baa2-07e47f2efe11, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=9d2c5ffd-b048-4026-a837-1fb688e37e19
e8ac2ac7-90f8-4293-8c5e-6d600cf8b2b8	2025-12-26 13:46:18.922543+05:30	Exotel API Error	Target=ae933b5e-d978-41af-a84c-318707568046, CallID=70da8d3e-c34d-42b9-bbf2-b2f217872439, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=597ee2e6-e0e0-4462-aeae-5548030b9493
e981365a-b202-4c36-88c4-a78347cbc1b5	2025-12-26 13:46:21.608123+05:30	Exotel API Error	Target=6987a34c-00ca-48f8-be7e-c5a496413024, CallID=0c68e090-b91b-4f83-ad92-75584ad07621, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=a09d5c7a-ecdd-4128-8ab6-5445e51fb299
28f765e8-f111-4124-aab2-6ebe137c7027	2025-12-26 13:46:21.608123+05:30	Exotel API Error	Target=3d6bd109-6078-477e-8a9c-54ecc4b6d130, CallID=eef88f62-1708-4124-8731-7f8497083c59, Error=403 Client Error: Forbidden for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=957cfd71-1921-40b1-ae50-8c8d5ecd639c
f03328d7-eadb-463f-a225-aee89a877d74	2025-12-26 13:46:21.608123+05:30	Exotel API Error	Target=55889035-11d3-4400-94a0-2ce02298336b, CallID=56a392be-6ff3-432e-89b0-66acc6a99809, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=7c3def60-3d88-4057-8da6-653edb461e60
65fc2b89-213c-4598-89f5-9a775fe96945	2025-12-26 13:46:21.608123+05:30	Exotel API Error	Target=38091e53-1fc9-4ed8-aba9-7bf7dd84ebde, CallID=0e8c86e2-6187-469f-896f-1544ffd41881, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=6e2334bd-0869-4365-a456-344be46e1829
541a26da-3c73-4549-967f-09a185a71872	2025-12-26 13:47:20.21025+05:30	Exotel API Error	Target=d86706cf-17bf-41d4-9261-84702426c685, CallID=d01903e3-a6eb-41e1-8bc2-40752412b6e6, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=6f934a8a-9769-4fa3-908c-0f6dfcb4e098
a69587de-e3a0-4240-9097-692a2684bb77	2025-12-26 13:47:20.21025+05:30	Exotel API Error	Target=1ecd196f-b293-4d68-a1bf-84ee8c769f8d, CallID=fa026619-9266-4899-86ec-e600874b0076, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=46139b25-9d89-459e-8b60-78952fd96ee1
6ff54e6e-2dd9-4209-9739-0c5d4db9eb0e	2025-12-26 13:47:20.21025+05:30	Exotel API Error	Target=3d6bd109-6078-477e-8a9c-54ecc4b6d130, CallID=8eca186f-6929-4981-92f0-4dcd18351c81, Error=403 Client Error: Forbidden for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=553bd20e-9199-4632-ba64-8649e6f97168
7d4a8fbc-7fa8-4fcf-9b3b-8ac2d6819101	2025-12-26 13:47:20.21025+05:30	Exotel API Error	Target=bc74c40e-1e3b-4e66-ae88-dd707d28add4, CallID=f1931143-d2e8-44dd-8dd1-1c07f9d46b33, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=5a49b8b0-e697-421e-bfac-5fc7c0d9fbb4
5a3b909d-c093-405b-8f3d-e8381ce691fe	2025-12-26 13:47:22.675021+05:30	Exotel API Error	Target=2dce29b3-9427-43db-b45d-c7f189061fb3, CallID=2af048ee-2476-4835-baa2-07e47f2efe11, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=94e247ac-59da-4ff4-b387-4f3471534a95
da5014bc-92d4-46cb-bef9-577eb2d34032	2025-12-26 13:47:22.675021+05:30	Exotel API Error	Target=ae933b5e-d978-41af-a84c-318707568046, CallID=70da8d3e-c34d-42b9-bbf2-b2f217872439, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=2cec4519-319e-4e70-9982-99a7af856946
ddae33d1-81fe-4b1f-8e92-4b475912cdf3	2025-12-26 13:47:22.677727+05:30	Exotel API Error	Target=d7120049-e0ce-48fd-9ed6-4a2802af1c42, CallID=5202b8a0-7178-4d23-8293-baa6ca434c4a, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=6fdb978e-655e-42d8-9740-4291108d4f18
44923bb4-7e63-4f5c-b357-0b7a3bb407f4	2025-12-26 13:47:22.679856+05:30	Exotel API Error	Target=543e37a6-78e7-4825-9ebc-561bef1a096c, CallID=87319e7d-cfb9-48d6-af00-4a0357f03500, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=2bb28af7-52a2-42cb-bff9-1c64cce97dba
3274fd47-6c2a-4482-967c-95aa95bac322	2025-12-26 13:47:25.378636+05:30	Exotel API Error	Target=6987a34c-00ca-48f8-be7e-c5a496413024, CallID=0c68e090-b91b-4f83-ad92-75584ad07621, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=ed018e4a-c233-4274-8547-cc4d10abb718
84580905-9159-4d9b-885b-c6ff5796b32e	2025-12-26 13:47:25.386099+05:30	Exotel API Error	Target=3d6bd109-6078-477e-8a9c-54ecc4b6d130, CallID=eef88f62-1708-4124-8731-7f8497083c59, Error=403 Client Error: Forbidden for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=ea04baae-e180-483e-ac61-bcf71ae5a171
77666d03-a5cf-4ca9-94af-e8949067b49c	2025-12-26 13:47:25.387169+05:30	Exotel API Error	Target=38091e53-1fc9-4ed8-aba9-7bf7dd84ebde, CallID=0e8c86e2-6187-469f-896f-1544ffd41881, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=de209798-4db4-4819-9fec-e242e5dab42b
1e49eed4-40b5-4b61-8965-247a8e695214	2025-12-26 13:47:25.393549+05:30	Exotel API Error	Target=55889035-11d3-4400-94a0-2ce02298336b, CallID=56a392be-6ff3-432e-89b0-66acc6a99809, Error=400 Client Error: Bad Request for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=e746982a-0fcb-487f-a294-b00574433133
dff1c465-0a79-442c-a58d-c7b6cbb251ed	2025-12-29 12:54:08.210266+05:30	Exotel API Error	Target=e471c565-30cd-434a-9601-ea25eb46bc11, CallID=0e4e55f1-30d7-41f7-b0a9-3524556fc540, Error=503 Server Error: Service Unavailable for url: https://api.exotel.com/v1/Accounts/iitgandhinagar1/Calls/connect.json, CorrelationID=ce22f251-888a-4be2-8785-3893657d7c3e
817b7b5d-0767-464e-a339-9ebdaf61637f	2025-12-30 02:09:37.491363+05:30	Emotion Processing Error	CallID=62e5ebbe-6248-45c2-90b9-83d96d3e3445, Error=Call record or recording not found for 62e5ebbe-6248-45c2-90b9-83d96d3e3445
\.


--
-- TOC entry 5091 (class 0 OID 16615)
-- Dependencies: 227
-- Data for Name: FlaggedTargets; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."FlaggedTargets" ("Flag_Id", "Target_Id", "Call_Scheduled_DateTime") FROM stdin;
\.


--
-- TOC entry 5088 (class 0 OID 16427)
-- Dependencies: 224
-- Data for Name: Models; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Models" ("Model_Id", "Model_Name", "Model_Version", "Model_Details") FROM stdin;
M001	Wav2Vec2	1.0	Wav2Vec2 model details ...
\.


--
-- TOC entry 5092 (class 0 OID 40964)
-- Dependencies: 228
-- Data for Name: Password_Reset_Tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Password_Reset_Tokens" ("Token_Id", "Admin_Id", "Token", "Created_At", "Expires_At", "Used") FROM stdin;
1fd68c8a-d336-47d8-b4a1-df9ab404b9d2	83686ba9-745b-400e-8ef9-49dd025ec658	nCapKUHa_V3mv8WFeftzsmPjJ2c6BMGlSgPgoRtHfdc	2026-01-21 11:48:16.95172+05:30	2026-01-22 11:48:16.878639+05:30	1
\.


--
-- TOC entry 5089 (class 0 OID 16459)
-- Dependencies: 225
-- Data for Name: Targets; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Targets" ("Target_Id", "Name", "Department_Name", "Program", "Roll_No", "Phone_No") FROM stdin;
f60c46db-5c8e-42d6-8d5e-388a99ffa943	Prabhakar Mishra	Mechanical	BTech	24250079	1234567990
7f401fee-e71f-4d01-858b-19b99e959eed	Suresh Sinha	Chemical	BTech	24250098	1234567890
e471c565-30cd-434a-9601-ea25eb46bc11	Aditya Srivastava	Computer Science	MTech	24250086	9369049853
c6da7cd2-6aa5-4466-a007-b914f8d4f73c	Raj Sharma	Civil	BTech	22110084	1233445590
7944682e-0a17-44fe-83af-fe00defcfcaa	Sneha Sharma	Electrical	B.Tech	22240019	9988776655
\.


--
-- TOC entry 5084 (class 0 OID 16395)
-- Dependencies: 220
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
20260227_add_analysis_score
\.


--
-- TOC entry 4905 (class 2606 OID 16410)
-- Name: Admins Admins_Email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Admins"
    ADD CONSTRAINT "Admins_Email_key" UNIQUE ("Email");


--
-- TOC entry 4907 (class 2606 OID 16408)
-- Name: Admins Admins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Admins"
    ADD CONSTRAINT "Admins_pkey" PRIMARY KEY ("Admin_Id");


--
-- TOC entry 4923 (class 2606 OID 16489)
-- Name: Calls Calls_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Calls"
    ADD CONSTRAINT "Calls_pkey" PRIMARY KEY ("Call_Id");


--
-- TOC entry 4909 (class 2606 OID 16418)
-- Name: Emotions Emotions_Emotion_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Emotions"
    ADD CONSTRAINT "Emotions_Emotion_key" UNIQUE ("Emotion");


--
-- TOC entry 4911 (class 2606 OID 16556)
-- Name: Emotions Emotions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Emotions"
    ADD CONSTRAINT "Emotions_pkey" PRIMARY KEY ("Emotion_Id");


--
-- TOC entry 4913 (class 2606 OID 16426)
-- Name: Error_Logs Error_Logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Error_Logs"
    ADD CONSTRAINT "Error_Logs_pkey" PRIMARY KEY ("Logs_Id");


--
-- TOC entry 4927 (class 2606 OID 16621)
-- Name: FlaggedTargets FlaggedTargets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."FlaggedTargets"
    ADD CONSTRAINT "FlaggedTargets_pkey" PRIMARY KEY ("Flag_Id");


--
-- TOC entry 4915 (class 2606 OID 16531)
-- Name: Models Models_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Models"
    ADD CONSTRAINT "Models_pkey" PRIMARY KEY ("Model_Id");


--
-- TOC entry 4929 (class 2606 OID 40974)
-- Name: Password_Reset_Tokens Password_Reset_Tokens_Token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Password_Reset_Tokens"
    ADD CONSTRAINT "Password_Reset_Tokens_Token_key" UNIQUE ("Token");


--
-- TOC entry 4931 (class 2606 OID 40972)
-- Name: Password_Reset_Tokens Password_Reset_Tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Password_Reset_Tokens"
    ADD CONSTRAINT "Password_Reset_Tokens_pkey" PRIMARY KEY ("Token_Id");


--
-- TOC entry 4917 (class 2606 OID 16466)
-- Name: Targets Targets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Targets"
    ADD CONSTRAINT "Targets_pkey" PRIMARY KEY ("Target_Id");


--
-- TOC entry 4903 (class 2606 OID 16400)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 4925 (class 2606 OID 16663)
-- Name: Calls uq_target_scheduled_time; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Calls"
    ADD CONSTRAINT uq_target_scheduled_time UNIQUE ("Target_Id", "Scheduled_Time");


--
-- TOC entry 4919 (class 2606 OID 24597)
-- Name: Targets uq_targets_phone_no; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Targets"
    ADD CONSTRAINT uq_targets_phone_no UNIQUE ("Phone_No");


--
-- TOC entry 4921 (class 2606 OID 24587)
-- Name: Targets uq_targets_roll_no; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Targets"
    ADD CONSTRAINT uq_targets_roll_no UNIQUE ("Roll_No");


--
-- TOC entry 4932 (class 2606 OID 16571)
-- Name: Calls Calls_Emotion_Id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Calls"
    ADD CONSTRAINT "Calls_Emotion_Id_fkey" FOREIGN KEY ("Emotion_Id") REFERENCES public."Emotions"("Emotion_Id");


--
-- TOC entry 4933 (class 2606 OID 16547)
-- Name: Calls Calls_Model_Id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Calls"
    ADD CONSTRAINT "Calls_Model_Id_fkey" FOREIGN KEY ("Model_Id") REFERENCES public."Models"("Model_Id");


--
-- TOC entry 4934 (class 2606 OID 16504)
-- Name: Calls Calls_Target_Id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Calls"
    ADD CONSTRAINT "Calls_Target_Id_fkey" FOREIGN KEY ("Target_Id") REFERENCES public."Targets"("Target_Id");


--
-- TOC entry 4935 (class 2606 OID 16622)
-- Name: FlaggedTargets FlaggedTargets_Target_Id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."FlaggedTargets"
    ADD CONSTRAINT "FlaggedTargets_Target_Id_fkey" FOREIGN KEY ("Target_Id") REFERENCES public."Targets"("Target_Id");


--
-- TOC entry 4936 (class 2606 OID 40975)
-- Name: Password_Reset_Tokens Password_Reset_Tokens_Admin_Id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Password_Reset_Tokens"
    ADD CONSTRAINT "Password_Reset_Tokens_Admin_Id_fkey" FOREIGN KEY ("Admin_Id") REFERENCES public."Admins"("Admin_Id");


-- Completed on 2026-02-27 09:18:12

--
-- PostgreSQL database dump complete
--

\unrestrict QhHVaWku6nqqevzSIwNRhooHmIwWTffgRkrRXzfvVUeFcJp326QG3NIKufHvBjV

