# Payymo System Architecture

## Version: 1.0 (April 15, 2025)

## 1. System Overview

### 1.1 Purpose
Payymo is a financial reconciliation system that automates the matching of bank transactions and payment gateway charges with invoices in billing systems, specifically targeting WHMCS integration. The system bridges the gap between payment providers and billing systems to reduce manual reconciliation work.

### 1.2 High-Level Architecture

```
┌────────────────┐     ┌───────────────┐     ┌───────────────────┐
│  Payment APIs  │     │  Payymo Core  │     │ WHMCS Integration │
│ (Open Banking, │◄───►│  (Processing, │◄───►│  (Module, API,    │
│  Stripe, etc.) │     │   Matching)   │     │   Webhooks)       │
└────────────────┘     └───────────────┘     └───────────────────┘
                              ▲
                              │
                              ▼
                       ┌─────────────┐
                       │  Admin UI   │
                       │ (Dashboard, │
                       │  Controls)  │
                       └─────────────┘
```

### 1.3 Core Components
1. **Authentication System**: Secure JWT-based authentication with RBAC
2. **Multi-tenant Framework**: Isolation for different WHMCS instances
3. **Banking Integration**: GoCardless Open Banking API integration
4. **Payment Gateway Integration**: Stripe API integration
5. **Matching Engine**: Algorithm to match transactions with invoices
6. **Admin Dashboard**: NobleUI-based interface for management
7. **WHMCS Module**: Integration with WHMCS billing system

## 2. Component Architecture

### 2.1 Authentication System

#### 2.1.1 Components
- **Auth Service**: Core authentication logic
- **JWT Provider**: Token generation and verification
- **RBAC Manager**: Role and permission management
- **Auth Middleware**: Request authentication validation

#### 2.1.2 Authentication Flow
```
┌──────────┐      ┌──────────┐      ┌───────────┐      ┌──────────┐
│  Client  │──1──►│  Login   │──2──►│  Generate │──3──►│  Client  │
│          │      │ Endpoint │      │   Tokens  │      │          │
└──────────┘      └──────────┘      └───────────┘      └──────────┘
     │                                                       │
     │              ┌───────────┐      ┌──────────┐         │
     └───────4─────►│ Protected │◄─5──►│  Verify  │◄────6───┘
                    │ Resource  │      │   Token  │
                    └───────────┘      └──────────┘
```

1. Client sends credentials to login endpoint
2. Auth service validates credentials
3. JWT tokens are generated and returned to client
4. Client requests protected resource with access token
5. Auth middleware verifies token with JWT provider
6. If token is valid, the request is processed

#### 2.1.3 JWT Structure
- **Access Token Claims**:
  - `iss`: Issuing authority (Payymo)
  - `sub`: Subject (user ID)
  - `aud`: Audience (api access)
  - `exp`: Expiration time
  - `nbf`: Not before time
  - `iat`: Issued at time
  - `jti`: JWT ID (for revocation)
  - `tenant_id`: Tenant identifier
  - `permissions`: RBAC permissions array

- **Refresh Token Claims**: 
  - Similar to access token but with different `aud` (refresh) and longer expiration

#### 2.1.4 Security Features
- RS256 asymmetric cryptography for signatures
- Token revocation tracking
- Anti-timing attack protection
- Rate limiting
- Input validation and sanitization

### 2.2 Multi-tenant Framework

#### 2.2.1 Components
- **Tenant Service**: Tenant management
- **Tenant Middleware**: Request tenant resolution
- **Tenant-aware Repository**: Data access with tenant isolation

#### 2.2.2 Tenant Isolation
- Database-level isolation with tenant_id foreign keys
- Request middleware that sets current tenant context
- Service-level validation of tenant access
- RBAC permissions specific to tenant resources

### 2.3 Banking Integration

#### 2.3.1 Components
- **GoCardless Service**: API interaction with GoCardless
- **Bank Connection Manager**: Connection setup and management
- **Transaction Fetcher**: Regular transaction fetching
- **Transaction Storage**: Database storage and indexing

#### 2.3.2 Banking Flow
```
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  Initiate│    │ Authorize │    │  Callback │    │  Store    │
│ Connection│───►│   with   │───►│  Process  │───►│ Connection │
│           │    │   Bank   │    │           │    │           │
└──────────┘    └───────────┘    └───────────┘    └───────────┘
                                                        │
                                                        ▼
                                                  ┌───────────┐
                                                  │  Fetch    │
                                                  │Transactions│
                                                  │           │
                                                  └───────────┘
                                                        │
                                                        ▼
                                                  ┌───────────┐
                                                  │  Match    │
                                                  │  Engine   │
                                                  │           │
                                                  └───────────┘
```

### 2.4 Payment Gateway Integration

#### 2.4.1 Components
- **Stripe Service**: API interaction with Stripe
- **Payment Processor**: Payment processing logic
- **Webhook Handler**: Processing Stripe events
- **Payment Storage**: Database storage and indexing

#### 2.4.2 Stripe Integration Flow
```
┌──────────┐    ┌───────────┐    ┌───────────┐   
│  Connect │    │ Authorize │    │  Store    │   
│  Stripe  │───►│ OAuth Flow│───►│ Connection │   
│          │    │           │    │           │   
└──────────┘    └───────────┘    └───────────┘   
                                       │
                                       ▼
                                 ┌───────────┐    ┌───────────┐
                                 │  Webhook  │    │  Process  │
                                 │  Events   │◄───│ Payments  │
                                 │           │    │           │
                                 └───────────┘    └───────────┘
                                       │
                                       ▼
                                 ┌───────────┐
                                 │  Match    │
                                 │  Engine   │
                                 │           │
                                 └───────────┘
```

### 2.5 Matching Engine

#### 2.5.1 Components
- **Matching Service**: Core matching logic
- **Rule Engine**: Configurable matching rules
- **Confidence Calculator**: Determines match confidence
- **Match Repository**: Stores and retrieves matches

#### 2.5.2 Matching Algorithm
1. Extract key data from transaction (amount, date, reference, etc.)
2. Query WHMCS for potential matching invoices
3. Apply matching rules to calculate confidence score
4. Store matches above threshold for review
5. Auto-approve high-confidence matches (configurable)

```
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│ Extract  │    │  Query    │    │  Apply    │    │ Calculate │
│Transaction│───►│ Potential │───►│ Matching  │───►│ Confidence│
│   Data   │    │  Invoices │    │   Rules   │    │   Score   │
└──────────┘    └───────────┘    └───────────┘    └───────────┘
                                                        │
                                                        ▼
                                                  ┌───────────┐
                                                  │  Store    │
                                                  │  Match    │
                                                  │           │
                                                  └───────────┘
```

### 2.6 Admin Dashboard

#### 2.6.1 Components
- **Dashboard UI**: NobleUI-based interface
- **Admin API**: Backend endpoints for admin functions
- **Reporting Engine**: Generates reports and insights
- **Audit Logger**: Tracks system and user actions

#### 2.6.2 Dashboard Features
- Transaction monitoring and management
- Match review and approval
- Bank and payment gateway connection management
- User and tenant administration
- System health monitoring
- Reporting and analytics

### 2.7 WHMCS Module

#### 2.7.1 Components
- **WHMCS API Client**: Communicates with WHMCS API
- **Webhook Receiver**: Processes WHMCS webhooks
- **Module Installer**: Installation and configuration
- **Admin Interface**: WHMCS admin area integration

#### 2.7.2 Integration Points
- Invoice data synchronization
- Payment notification
- Match status updates
- Configuration management

## 3. Data Architecture

### 3.1 Database Schema

#### 3.1.1 Core Tables
- **users**: User authentication and profiles
- **permissions**: RBAC permissions
- **roles**: User roles
- **token_revocations**: Revoked JWT tokens

#### 3.1.2 Tenant Management
- **license_keys**: License key validation
- **whmcs_instances**: Connected WHMCS instances

#### 3.1.3 Banking Integration
- **bank_connections**: Bank account connections
- **transactions**: Bank transaction data

#### 3.1.4 Payment Gateway Integration
- **stripe_connections**: Stripe account connections
- **stripe_payments**: Stripe payment data

#### 3.1.5 Matching System
- **invoice_matches**: Transaction-invoice matches
- **stripe_invoice_matches**: Stripe payment-invoice matches
- **matching_rules**: Configurable matching rules

### 3.2 Data Flow

```
┌────────────┐    ┌────────────┐    ┌────────────┐
│  External  │    │  Payymo    │    │   WHMCS    │
│   APIs     │───►│  Database  │◄───┤  System    │
│            │    │            │    │            │
└────────────┘    └────────────┘    └────────────┘
      │                 ▲                 ▲
      │                 │                 │
      │           ┌────────────┐         │
      └──────────►│  Matching  │─────────┘
                  │   Engine   │
                  │            │
                  └────────────┘
```

## 4. Security Architecture

### 4.1 Authentication
- JWT authentication with RS256 algorithm
- Refresh token rotation
- Session management and token revocation
- Rate limiting and brute force protection

### 4.2 Authorization
- Role-Based Access Control (RBAC)
- Permission-based resource access
- Tenant isolation
- API key authentication for service-to-service calls

### 4.3 Data Protection
- TLS for all communications
- Data encryption at rest for sensitive data
- Certificate validation for API communications
- Input validation and sanitization

### 4.4 Secrets Management
- Centralized secrets service
- Environment-aware secrets handling
- Key rotation capabilities
- Circuit breakers for missing secrets

## 5. Integration Architecture

### 5.1 External APIs
- **GoCardless Open Banking API**: Bank connections and transactions
- **Stripe API**: Payment processing and management
- **WHMCS API**: Invoice and client data

### 5.2 Webhooks
- **Stripe Webhooks**: Payment notifications
- **GoCardless Webhooks**: Banking events
- **WHMCS Webhooks**: Invoice and client events

### 5.3 API Gateway
- Authentication and authorization
- Rate limiting
- Request validation
- Response formatting

## 6. Deployment Architecture

### 6.1 Environment Setup
- **Development**: Local development environment
- **Testing**: Automated test environment
- **Staging**: Pre-production environment
- **Production**: Live environment

### 6.2 Infrastructure
- **Application Server**: Flask with Gunicorn
- **Database**: PostgreSQL
- **Caching**: Redis (planned)
- **Scheduled Tasks**: Celery (planned)

### 6.3 Scalability Considerations
- Horizontal scaling of application servers
- Database read replicas
- Caching layer for frequent queries
- Asynchronous processing for background tasks

## 7. Future Architecture Enhancements

### 7.1 Planned Improvements
- Microservice architecture for key components
- Event-driven architecture for transaction processing
- Machine learning for improved matching accuracy
- Real-time analytics dashboard

### 7.2 Technical Debt Resolution
- Standardize service interfaces
- Implement dependency injection
- Add comprehensive integration testing
- Create CI/CD validation pipelines

## 8. References

### 8.1 Internal Documentation
- **Remediation Plan**: `project_management/REMEDIATION_PLAN.md`
- **Roadmap**: `project_management/ROADMAP.md`
- **Security Documentation**: `project_management/security/`

### 8.2 External Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [JWT Specification](https://datatracker.ietf.org/doc/html/rfc7519)
- [GoCardless API Documentation](https://developer.gocardless.com/api-reference/)
- [Stripe API Documentation](https://stripe.com/docs/api)

---

**Document Revision History**
- v1.0 (April 15, 2025): Initial architecture document