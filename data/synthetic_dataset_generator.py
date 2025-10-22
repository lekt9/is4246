"""
AFAAP Synthetic Dataset Generator

Generates realistic synthetic data for testing the governance framework:
- Users across all three lines of defense
- Models with varying performance characteristics
- 10,000+ transactions with edge cases:
  - High-frequency traders
  - Cross-border transactions
  - Same-day reversals
  - Various fraud patterns
- Fraud detection decisions with human reviews
- Re-validation workflows
- Failure incidents

Edge cases included:
- High-value transactions ($1M+)
- Micro-transactions (<$10)
- Same-day reversals
- Cross-border high-risk corridors
- Legitimate transactions that look suspicious
- Fraud that evades detection (false negatives)
"""

import os
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Tuple
import psycopg2
from psycopg2.extras import execute_batch
from faker import Faker
import hashlib
import json

# Initialize Faker for generating realistic data
fake = Faker()
Faker.seed(42)  # For reproducibility
random.seed(42)

# Database connection from environment or default
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://afaap_admin:afaap_password@localhost:5432/afaap'
)

# Constants
TRANSACTION_TYPES = [
    'wire_transfer',
    'credit_card',
    'ach',
    'check',
    'atm_withdrawal',
    'mobile_payment',
    'cryptocurrency'
]

COUNTRIES = ['SGP', 'USA', 'GBR', 'CHN', 'JPN', 'IND', 'AUS', 'HKG', 'MYS', 'THA', 'VNM', 'IDN']
HIGH_RISK_COUNTRIES = ['XXX', 'YYY', 'ZZZ']  # Fictional high-risk jurisdictions

CUSTOMER_SEGMENTS = ['retail', 'corporate', 'institutional', 'private_banking']
RISK_PROFILES = ['low', 'medium', 'high']

FRAUD_TYPES = [
    'account_takeover',
    'credit_card_fraud',
    'wire_fraud',
    'money_laundering',
    'identity_theft',
    'synthetic_identity',
    'business_email_compromise',
    'check_kiting'
]

OFFICER_DECISIONS = [
    'approve_transaction',
    'block_transaction',
    'escalate',
    'false_positive'
]


class SyntheticDataGenerator:
    """Generate synthetic data for AFAAP governance framework testing."""

    def __init__(self, database_url: str = DATABASE_URL):
        """Initialize generator with database connection."""
        self.database_url = database_url
        self.conn = None
        self.cur = None

        # Track created entity IDs for foreign key relationships
        self.user_ids: Dict[str, str] = {}
        self.role_ids: Dict[str, int] = {}
        self.model_ids: List[str] = []
        self.transaction_ids: List[str] = []
        self.decision_ids: List[str] = []

    def connect(self):
        """Establish database connection."""
        self.conn = psycopg2.connect(self.database_url)
        self.cur = self.conn.cursor()
        print(f"Connected to database: {self.database_url.split('@')[1]}")

    def disconnect(self):
        """Close database connection."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed.")

    def set_session_user(self, user_id: str):
        """Set current user for audit trail attribution."""
        self.cur.execute(f"SET app.current_user_id = '{user_id}';")
        self.cur.execute(f"SET app.session_id = '{uuid.uuid4()}';")

    def get_role_ids(self):
        """Fetch existing role IDs from database."""
        self.cur.execute("SELECT role_id, role_name FROM roles;")
        for role_id, role_name in self.cur.fetchall():
            self.role_ids[role_name] = role_id
        print(f"Fetched {len(self.role_ids)} roles from database.")

    def generate_users(self, num_developers: int = 5, num_officers: int = 10,
                      num_auditors: int = 3, num_admins: int = 2):
        """Generate user accounts across all roles."""
        users_data = []

        # Generate developers (first line of defense)
        for i in range(num_developers):
            user_id = str(uuid.uuid4())
            self.user_ids[f'developer_{i}'] = user_id
            users_data.append((
                user_id,
                f'dev_{fake.user_name()}',
                fake.email(),
                self.role_ids['developer'],
                'hashed_password_placeholder',  # In production, use bcrypt
                True,
                datetime.now(),
                None,  # last_login
                None   # created_by
            ))

        # Generate compliance officers (second line of defense)
        for i in range(num_officers):
            user_id = str(uuid.uuid4())
            self.user_ids[f'officer_{i}'] = user_id
            users_data.append((
                user_id,
                f'officer_{fake.user_name()}',
                fake.email(),
                self.role_ids['compliance_officer'],
                'hashed_password_placeholder',
                True,
                datetime.now(),
                None,
                None
            ))

        # Generate auditors (third line of defense)
        for i in range(num_auditors):
            user_id = str(uuid.uuid4())
            self.user_ids[f'auditor_{i}'] = user_id
            users_data.append((
                user_id,
                f'auditor_{fake.user_name()}',
                fake.email(),
                self.role_ids['auditor'],
                'hashed_password_placeholder',
                True,
                datetime.now(),
                None,
                None
            ))

        # Generate admins
        for i in range(num_admins):
            user_id = str(uuid.uuid4())
            self.user_ids[f'admin_{i}'] = user_id
            users_data.append((
                user_id,
                f'admin_{fake.user_name()}',
                fake.email(),
                self.role_ids['admin'],
                'hashed_password_placeholder',
                True,
                datetime.now(),
                None,
                None
            ))

        # Insert users
        insert_query = """
            INSERT INTO users (
                user_id, username, email, role_id, hashed_password,
                is_active, created_at, last_login, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING;
        """
        execute_batch(self.cur, insert_query, users_data)
        self.conn.commit()

        # Re-query to get actual inserted user IDs (some may have been skipped due to conflicts)
        self.user_ids = {}

        # Get developers
        self.cur.execute("""
            SELECT u.user_id FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE r.role_name = 'developer'
            ORDER BY u.created_at
            LIMIT %s
        """, (num_developers,))
        for i, row in enumerate(self.cur.fetchall()):
            self.user_ids[f'developer_{i}'] = row[0]

        # Get officers
        self.cur.execute("""
            SELECT u.user_id FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE r.role_name = 'compliance_officer'
            ORDER BY u.created_at
            LIMIT %s
        """, (num_officers,))
        for i, row in enumerate(self.cur.fetchall()):
            self.user_ids[f'officer_{i}'] = row[0]

        # Get auditors
        self.cur.execute("""
            SELECT u.user_id FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE r.role_name = 'auditor'
            ORDER BY u.created_at
            LIMIT %s
        """, (num_auditors,))
        for i, row in enumerate(self.cur.fetchall()):
            self.user_ids[f'auditor_{i}'] = row[0]

        # Get admins
        self.cur.execute("""
            SELECT u.user_id FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE r.role_name = 'admin'
            ORDER BY u.created_at
            LIMIT %s
        """, (num_admins,))
        for i, row in enumerate(self.cur.fetchall()):
            self.user_ids[f'admin_{i}'] = row[0]

        print(f"Generated {len(users_data)} users across all roles (actual inserted: {len(self.user_ids)}).")

    def generate_models(self, num_models: int = 5):
        """Generate AI/ML models with varying performance characteristics."""
        models_data = []
        developer_id = self.user_ids['developer_0']
        officer_id = self.user_ids['officer_0']
        auditor_id = self.user_ids['auditor_0']

        # Verify developer exists before setting session
        self.cur.execute("SELECT user_id FROM users WHERE user_id = %s", (developer_id,))
        if not self.cur.fetchone():
            raise ValueError(f"Developer user {developer_id} not found in database")

        self.set_session_user(developer_id)

        model_configs = [
            # High-performing model (exceeds thresholds)
            {
                'name': 'fraud_detector_v1',
                'f1': 0.89,
                'fpr': 0.008,
                'status': 'deployed',
                'fraud_types': ['credit_card_fraud', 'wire_fraud']
            },
            # Borderline model (just meets thresholds)
            {
                'name': 'fraud_detector_v2',
                'f1': 0.85,
                'fpr': 0.01,
                'status': 'deployed',
                'fraud_types': ['account_takeover', 'identity_theft']
            },
            # Underperforming model (below threshold)
            {
                'name': 'fraud_detector_beta',
                'f1': 0.82,
                'fpr': 0.015,
                'status': 'under_review',
                'fraud_types': ['money_laundering']
            },
            # Specialized model (high precision, lower recall)
            {
                'name': 'high_value_wire_detector',
                'f1': 0.87,
                'fpr': 0.005,
                'status': 'deployed',
                'fraud_types': ['wire_fraud', 'business_email_compromise']
            },
            # Experimental model (pending approval)
            {
                'name': 'ml_ensemble_v1',
                'f1': 0.91,
                'fpr': 0.009,
                'status': 'pending_approval',
                'fraud_types': ['synthetic_identity', 'account_takeover']
            }
        ]

        for i, config in enumerate(model_configs[:num_models]):
            model_id = str(uuid.uuid4())
            self.model_ids.append(model_id)

            # Calculate precision and recall from F1
            # F1 = 2 * (precision * recall) / (precision + recall)
            # For realistic values, slightly vary precision/recall around F1
            precision = min(0.99, config['f1'] + random.uniform(-0.02, 0.05))
            # Calculate recall from F1 and precision
            # recall = (F1 * precision) / (2 * precision - F1)
            if precision > config['f1']:
                recall = (config['f1'] * precision) / (2 * precision - config['f1'])
            else:
                recall = precision
            recall = min(0.99, max(0.01, recall))  # Clamp to valid range
            auc_roc = 0.95 + random.uniform(-0.05, 0.03)

            # Confidence intervals (bootstrap simulation)
            f1_ci_lower = max(0, config['f1'] - 0.03)
            f1_ci_upper = min(1, config['f1'] + 0.02)
            fpr_ci_lower = max(0, config['fpr'] - 0.002)
            fpr_ci_upper = min(1, config['fpr'] + 0.003)

            # Training dates (last 6 months)
            training_end = datetime.now() - timedelta(days=random.randint(30, 180))
            training_start = training_end - timedelta(days=90)

            models_data.append((
                model_id,
                config['name'],
                f'v{i+1}.0.0',
                f"Fraud detection model targeting {', '.join(config['fraud_types'])}",
                f"transactions_2024_q{random.randint(1,4)}_production",
                training_start.date(),
                training_end.date(),
                random.randint(50000, 200000),  # training record count
                Decimal(str(round(config['f1'], 4))),
                Decimal(str(round(config['fpr'], 4))),
                Decimal(str(round(precision, 4))),
                Decimal(str(round(recall, 4))),
                Decimal(str(round(auc_roc, 4))),
                Decimal(str(round(f1_ci_lower, 4))),
                Decimal(str(round(f1_ci_upper, 4))),
                Decimal(str(round(fpr_ci_lower, 4))),
                Decimal(str(round(fpr_ci_upper, 4))),
                None,  # parent_model_id
                random.choice(['random_forest', 'gradient_boosting', 'neural_network', 'ensemble']),
                config['fraud_types'],
                config['status'],
                training_end if config['status'] in ['deployed', 'under_review'] else None,
                None,  # retirement_date
                developer_id,
                officer_id if config['status'] != 'pending_approval' else None,
                auditor_id if config['status'] == 'deployed' else None,
                datetime.now(),
                datetime.now()
            ))

        insert_query = """
            INSERT INTO models (
                model_id, name, version, description,
                training_data_provenance, training_start_date, training_end_date,
                training_record_count, f1_score, fpr, precision_score, recall_score,
                auc_roc, f1_ci_lower, f1_ci_upper, fpr_ci_lower, fpr_ci_upper,
                parent_model_id, model_type, fraud_types_targeted,
                status, deployment_date, retirement_date,
                developed_by, approved_by, audited_by, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (name, version) DO NOTHING;
        """
        execute_batch(self.cur, insert_query, models_data)
        self.conn.commit()

        # Re-query to get actual model IDs
        self.model_ids = []
        self.cur.execute("SELECT model_id FROM models ORDER BY created_at")
        for row in self.cur.fetchall():
            self.model_ids.append(row[0])

        print(f"Generated {len(models_data)} models with varying performance (actual inserted: {len(self.model_ids)}).")

    def generate_transactions(self, num_transactions: int = 10000, fraud_rate: float = 0.05):
        """
        Generate financial transactions with realistic patterns and edge cases.

        Edge cases:
        - High-value transactions ($1M+)
        - Micro-transactions (<$10)
        - Cross-border high-risk corridors
        - High-frequency trading patterns
        - Same-day reversals
        """
        transactions_data = []
        num_fraud = int(num_transactions * fraud_rate)
        num_legitimate = num_transactions - num_fraud

        # Helper function to generate transaction
        def create_transaction(is_fraud_txn: bool) -> Tuple:
            txn_id = str(uuid.uuid4())
            self.transaction_ids.append(txn_id)

            # Transaction type distribution
            if is_fraud_txn:
                # Fraud more common in certain types
                txn_type = random.choices(
                    TRANSACTION_TYPES,
                    weights=[25, 30, 15, 10, 5, 10, 5],  # Higher for wire and credit card
                    k=1
                )[0]
            else:
                txn_type = random.choice(TRANSACTION_TYPES)

            # Amount distribution with edge cases
            if is_fraud_txn:
                # Fraud: mix of small tests and large thefts
                if random.random() < 0.3:
                    amount = Decimal(str(round(random.uniform(1, 50), 2)))  # Test transactions
                elif random.random() < 0.6:
                    amount = Decimal(str(round(random.uniform(1000, 50000), 2)))  # Medium
                else:
                    amount = Decimal(str(round(random.uniform(100000, 5000000), 2)))  # Large theft
            else:
                # Legitimate: normal distribution with occasional large transfers
                if random.random() < 0.1:  # Edge case: micro-transaction
                    amount = Decimal(str(round(random.uniform(0.01, 10), 2)))
                elif random.random() < 0.85:  # Normal
                    amount = Decimal(str(round(random.gauss(5000, 10000), 2)))
                else:  # Edge case: high-value legitimate (corporate, real estate)
                    amount = Decimal(str(round(random.uniform(500000, 10000000), 2)))

            amount = max(Decimal('0.01'), amount)  # Ensure positive

            # Currency (SGD-centric with international)
            currency = random.choices(
                ['SGD', 'USD', 'EUR', 'GBP', 'JPY', 'CNY'],
                weights=[50, 25, 10, 5, 5, 5],
                k=1
            )[0]

            # Geography
            if is_fraud_txn and random.random() < 0.4:
                # Fraud: higher probability of high-risk corridors
                origin = random.choice(COUNTRIES + HIGH_RISK_COUNTRIES)
                destination = random.choice(COUNTRIES + HIGH_RISK_COUNTRIES)
            else:
                # Legitimate: mostly domestic or major trading partners
                if random.random() < 0.6:
                    origin = destination = 'SGP'  # Domestic
                else:
                    origin = random.choice(COUNTRIES)
                    destination = random.choice(COUNTRIES)

            # Customer profile
            segment = random.choices(
                CUSTOMER_SEGMENTS,
                weights=[60, 25, 10, 5],
                k=1
            )[0]

            if is_fraud_txn:
                risk_profile = random.choices(RISK_PROFILES, weights=[10, 40, 50], k=1)[0]
            else:
                risk_profile = random.choices(RISK_PROFILES, weights=[70, 25, 5], k=1)[0]

            # Transaction timestamp (last 6 months)
            days_ago = random.randint(0, 180)
            hours = random.randint(0, 23)
            minutes = random.randint(0, 59)
            txn_date = datetime.now() - timedelta(days=days_ago, hours=hours, minutes=minutes)

            # Ground truth (is_fraud)
            fraud_type = random.choice(FRAUD_TYPES) if is_fraud_txn else None

            # Verification timestamp (simulating investigation completion)
            verified_at = txn_date + timedelta(hours=random.randint(24, 720)) if random.random() < 0.7 else None
            verified_by = random.choice(list(self.user_ids.values())) if verified_at else None

            return (
                txn_id,
                f'TXN-{fake.bothify(text="##??####").upper()}',  # external_transaction_id
                txn_type,
                amount,
                currency,
                txn_date,
                origin,
                destination,
                segment,
                risk_profile,
                is_fraud_txn,
                fraud_type,
                verified_at,
                verified_by,
                datetime.now()
            )

        # Generate fraud transactions
        print(f"Generating {num_fraud} fraudulent transactions...")
        for _ in range(num_fraud):
            transactions_data.append(create_transaction(True))

        # Generate legitimate transactions
        print(f"Generating {num_legitimate} legitimate transactions...")
        for _ in range(num_legitimate):
            transactions_data.append(create_transaction(False))

        # Shuffle to mix fraud and legitimate
        random.shuffle(transactions_data)

        # Insert in batches for performance
        insert_query = """
            INSERT INTO transactions (
                transaction_id, external_transaction_id, transaction_type,
                amount, currency, transaction_date, origin_country, destination_country,
                customer_segment, customer_risk_profile, is_fraud, fraud_type,
                verified_at, verified_by, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (external_transaction_id) DO NOTHING;
        """

        batch_size = 1000
        for i in range(0, len(transactions_data), batch_size):
            batch = transactions_data[i:i+batch_size]
            execute_batch(self.cur, insert_query, batch)
            self.conn.commit()
            print(f"Inserted batch {i//batch_size + 1}/{(len(transactions_data)-1)//batch_size + 1}")

        # Re-query to get actual transaction IDs
        self.transaction_ids = []
        self.cur.execute("SELECT transaction_id FROM transactions ORDER BY created_at")
        for row in self.cur.fetchall():
            self.transaction_ids.append(row[0])

        print(f"Generated {len(transactions_data)} transactions ({num_fraud} fraud, {num_legitimate} legitimate, actual inserted: {len(self.transaction_ids)}).")

    def generate_decisions(self, coverage: float = 0.8):
        """
        Generate fraud detection decisions for transactions.

        coverage: Percentage of transactions that have been scored by models
        """
        decisions_data = []

        # Get deployed models
        deployed_models = [mid for mid in self.model_ids[:3]]  # First 3 are deployed
        if not deployed_models:
            print("No deployed models found, skipping decision generation.")
            return

        # Sample transactions for decision generation
        num_decisions = int(len(self.transaction_ids) * coverage)
        sampled_txn_ids = random.sample(self.transaction_ids, num_decisions)

        print(f"Generating {num_decisions} fraud detection decisions...")

        for txn_id in sampled_txn_ids:
            decision_id = str(uuid.uuid4())
            self.decision_ids.append(decision_id)

            # Select model (weighted toward first model)
            model_id = random.choices(deployed_models, weights=[0.6, 0.3, 0.1], k=1)[0]

            # Get ground truth for this transaction
            self.cur.execute(
                "SELECT is_fraud, fraud_type FROM transactions WHERE transaction_id = %s",
                (txn_id,)
            )
            result = self.cur.fetchone()
            actual_fraud = result[0] if result else None

            # Model prediction (with realistic error rates)
            if actual_fraud is True:
                # True fraud: model catches it 85% of the time (recall ~0.85)
                prediction_fraud = random.random() < 0.85
                confidence = random.uniform(0.7, 0.95) if prediction_fraud else random.uniform(0.3, 0.6)
            elif actual_fraud is False:
                # Legitimate: model correctly identifies 99% (FPR ~1%)
                prediction_fraud = random.random() < 0.01
                confidence = random.uniform(0.1, 0.4) if prediction_fraud else random.uniform(0.05, 0.3)
            else:
                # Unknown ground truth: model prediction based on risk
                prediction_fraud = random.random() < 0.1
                confidence = random.uniform(0.4, 0.8)

            # Model features (for explainability)
            model_features = {
                'amount_zscore': round(random.gauss(0, 1), 2),
                'velocity_24h': random.randint(1, 10),
                'country_risk_score': round(random.uniform(0, 1), 2),
                'time_since_last_txn_hours': random.randint(1, 720),
                'merchant_category_risk': round(random.uniform(0, 1), 2)
            }

            flag_timestamp = datetime.now() - timedelta(days=random.randint(0, 90))

            # Human review (compliance officer)
            # Higher probability of review for high-confidence fraud predictions
            needs_review = prediction_fraud and confidence > 0.6

            if needs_review and random.random() < 0.9:  # 90% review coverage for flagged
                reviewed_by = random.choice([
                    uid for key, uid in self.user_ids.items() if key.startswith('officer_')
                ])

                # Officer decision
                if actual_fraud is True and prediction_fraud:
                    # True positive: block
                    officer_decision = random.choices(
                        ['block_transaction', 'escalate'],
                        weights=[0.8, 0.2],
                        k=1
                    )[0]
                elif actual_fraud is False and prediction_fraud:
                    # False positive: approve or mark false positive
                    officer_decision = random.choices(
                        ['approve_transaction', 'false_positive', 'escalate'],
                        weights=[0.6, 0.3, 0.1],
                        k=1
                    )[0]
                elif actual_fraud is True and not prediction_fraud:
                    # False negative (caught in review): escalate
                    officer_decision = 'escalate'
                else:
                    # True negative: approve
                    officer_decision = 'approve_transaction'

                officer_notes = self._generate_officer_notes(officer_decision, confidence, actual_fraud)
                decision_timestamp = flag_timestamp + timedelta(hours=random.randint(1, 120))  # 1h-5days

                final_decision = {
                    'approve_transaction': 'approved',
                    'block_transaction': 'blocked',
                    'escalate': 'escalated',
                    'false_positive': 'approved'
                }.get(officer_decision, 'pending')

                escalated_to = random.choice([
                    uid for key, uid in self.user_ids.items() if key.startswith('auditor_')
                ]) if officer_decision == 'escalate' else None

            else:
                reviewed_by = None
                officer_decision = None
                officer_notes = None
                decision_timestamp = None
                final_decision = 'pending'
                escalated_to = None

            # Compute audit trail hash
            hash_input = f"{model_id}|{txn_id}|{prediction_fraud}|{confidence}|{reviewed_by}|{officer_decision}"
            audit_trail_hash = hashlib.sha256(hash_input.encode()).hexdigest()

            # Audit trail complete if all review fields populated
            audit_trail_complete = all([
                reviewed_by is not None,
                officer_decision is not None,
                decision_timestamp is not None,
                officer_notes is not None
            ])

            decisions_data.append((
                decision_id,
                model_id,
                txn_id,
                prediction_fraud,
                Decimal(str(round(confidence, 4))),
                json.dumps(model_features),
                flag_timestamp,
                reviewed_by,
                officer_decision,
                officer_notes,
                decision_timestamp,
                final_decision,
                escalated_to,
                f"Escalation required for high-risk decision" if escalated_to else None,
                audit_trail_hash,
                audit_trail_complete,
                datetime.now(),
                datetime.now()
            ))

        # Insert decisions
        insert_query = """
            INSERT INTO decisions (
                decision_id, model_id, transaction_id, prediction_fraud,
                confidence_score, model_features, flag_timestamp,
                reviewed_by, officer_decision, officer_notes, decision_timestamp,
                final_decision, escalated_to, escalation_reason,
                audit_trail_hash, audit_trail_complete, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
        """

        batch_size = 1000
        for i in range(0, len(decisions_data), batch_size):
            batch = decisions_data[i:i+batch_size]
            execute_batch(self.cur, insert_query, batch)
            self.conn.commit()
            print(f"Inserted decision batch {i//batch_size + 1}/{(len(decisions_data)-1)//batch_size + 1}")

        print(f"Generated {len(decisions_data)} decisions.")

    def _generate_officer_notes(self, decision: str, confidence: float, actual_fraud: bool) -> str:
        """Generate realistic compliance officer notes."""
        templates = {
            'approve_transaction': [
                "Reviewed transaction details and customer history. Appears to be legitimate business activity.",
                "Customer contacted and verified transaction. Approved for processing.",
                "Low risk indicators despite model flag. Transaction approved.",
            ],
            'block_transaction': [
                "High fraud risk indicators confirmed. Transaction blocked pending investigation.",
                "Suspicious activity pattern detected. Customer unable to verify transaction. Blocked.",
                "Matches known fraud pattern. Transaction blocked and reported to fraud team.",
            ],
            'escalate': [
                "Requires senior review due to high value and unusual pattern.",
                "Customer verification inconclusive. Escalating to fraud investigation team.",
                "Complex case requiring additional analysis. Escalated to auditor.",
            ],
            'false_positive': [
                "False positive - customer provided documentation confirming legitimacy.",
                "Model incorrectly flagged legitimate business transaction. Marking as false positive for retraining.",
                "Reviewed with customer. Transaction legitimate. Model needs recalibration.",
            ]
        }
        return random.choice(templates.get(decision, ["Standard review completed."]))

    def generate_revalidation_workflows(self, num_workflows: int = 3):
        """Generate re-validation workflows for model repurposing."""
        workflows_data = []

        if not self.model_ids:
            print("No models available for revalidation workflows.")
            return

        trigger_reasons = [
            ('new_fraud_type', 'Model being extended to detect synthetic identity fraud'),
            ('performance_degradation', 'Production F1 score dropped to 0.82 over last 30 days'),
            ('data_distribution_shift', 'Significant shift in transaction patterns post-regulatory change'),
        ]

        for i in range(min(num_workflows, len(trigger_reasons))):
            revalidation_id = str(uuid.uuid4())
            model_id = random.choice(self.model_ids)
            trigger_reason, trigger_details = trigger_reasons[i]

            triggered_by = self.user_ids['developer_0']
            reviewed_by = self.user_ids['officer_0']
            approved_by = self.user_ids['auditor_0']

            # Simulate revalidation results
            revalidation_f1 = Decimal(str(round(random.uniform(0.84, 0.92), 4)))
            revalidation_fpr = Decimal(str(round(random.uniform(0.007, 0.012), 4)))
            test_set_size = random.randint(10000, 50000)

            status = 'approved' if revalidation_f1 >= 0.85 and revalidation_fpr <= 0.01 else 'requires_changes'

            workflows_data.append((
                revalidation_id,
                model_id,
                trigger_reason,
                trigger_details,
                datetime.now() - timedelta(days=random.randint(10, 60)),
                triggered_by,
                ['synthetic_identity', 'account_takeover'] if trigger_reason == 'new_fraud_type' else None,
                'transactions_2024_q4_updated' if trigger_reason != 'new_fraud_type' else 'synthetic_identity_dataset_v1',
                revalidation_f1,
                revalidation_fpr,
                test_set_size,
                f"https://internal-docs.example.com/revalidation/{revalidation_id}",
                status,
                reviewed_by,
                "Revalidation metrics reviewed and meet thresholds." if status == 'approved' else "F1 below threshold, requires model tuning.",
                datetime.now() - timedelta(days=random.randint(1, 30)),
                approved_by if status == 'approved' else None,
                datetime.now() - timedelta(days=random.randint(0, 10)) if status == 'approved' else None,
                "Approved for deployment with new fraud types." if status == 'approved' else None,
                datetime.now(),
                datetime.now()
            ))

        insert_query = """
            INSERT INTO revalidation_workflows (
                revalidation_id, model_id, trigger_reason, trigger_details,
                triggered_date, triggered_by, new_fraud_types, new_data_provenance,
                revalidation_f1_score, revalidation_fpr, revalidation_test_set_size,
                revalidation_report_url, status, reviewed_by, review_notes, review_date,
                approved_by, approval_date, approval_notes, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
        """
        execute_batch(self.cur, insert_query, workflows_data)
        self.conn.commit()
        print(f"Generated {len(workflows_data)} revalidation workflows.")

    def generate_failure_incidents(self, num_incidents: int = 5):
        """Generate failure incident records."""
        incidents_data = []

        if not self.model_ids:
            print("No models available for failure incidents.")
            return

        failure_scenarios = [
            {
                'type': 'false_positive_spike',
                'severity': 'high',
                'description': 'FPR increased from 0.8% to 2.1% over 48 hours due to holiday shopping surge.',
                'root_cause': 'Model trained on normal transaction volumes, not holiday patterns.',
                'category': 'data_distribution_shift',
                'responsible': 'developer',
            },
            {
                'type': 'performance_degradation',
                'severity': 'critical',
                'description': 'F1 score dropped from 0.89 to 0.79 in production monitoring.',
                'root_cause': 'New fraud pattern (synthetic identity) not represented in training data.',
                'category': 'model_drift',
                'responsible': 'financial_institution',
            },
            {
                'type': 'bias_detection',
                'severity': 'high',
                'description': 'FPR for cross-border transactions 15% higher than domestic.',
                'root_cause': 'Insufficient cross-border transaction representation in training set.',
                'category': 'training_data_bias',
                'responsible': 'developer',
            },
            {
                'type': 'system_error',
                'severity': 'medium',
                'description': 'Model inference timeout for 3% of high-value transactions.',
                'root_cause': 'Inefficient feature computation for transactions >$1M.',
                'category': 'performance_issue',
                'responsible': 'vendor',
            },
            {
                'type': 'false_negative_spike',
                'severity': 'critical',
                'description': 'Missed 12 fraudulent wire transfers totaling $2.4M over one week.',
                'root_cause': 'Fraudsters adapted to model by splitting large transfers.',
                'category': 'adversarial_attack',
                'responsible': 'external_factor',
            }
        ]

        for i in range(min(num_incidents, len(failure_scenarios))):
            incident_id = str(uuid.uuid4())
            scenario = failure_scenarios[i]
            model_id = random.choice(self.model_ids)

            detected_by = random.choice([
                uid for key, uid in self.user_ids.items()
                if key.startswith('developer_') or key.startswith('officer_')
            ])

            assigned_to = self.user_ids['developer_0'] if scenario['responsible'] == 'developer' else None
            auditor = self.user_ids['auditor_0']

            # Simulate incident lifecycle
            detected_date = datetime.now() - timedelta(days=random.randint(30, 120))
            remediation_status = random.choice(['in_progress', 'resolved', 'closed'])

            remediation_completed = None
            auditor_signoff_date = None

            if remediation_status == 'resolved':
                remediation_completed = detected_date + timedelta(days=random.randint(7, 30))
            elif remediation_status == 'closed':
                remediation_completed = detected_date + timedelta(days=random.randint(7, 30))
                auditor_signoff_date = remediation_completed + timedelta(days=random.randint(1, 7))

            incidents_data.append((
                incident_id,
                model_id,
                scenario['type'],
                scenario['severity'],
                scenario['description'],
                detected_date,
                detected_by,
                random.randint(100, 5000) if 'spike' in scenario['type'] else None,  # affected_transaction_count
                random.randint(50, 1000) if scenario['type'] == 'false_positive_spike' else None,  # fp_count
                random.randint(5, 50) if scenario['type'] == 'false_negative_spike' else None,  # fn_count
                Decimal(str(random.randint(10000, 5000000))) if scenario['severity'] == 'critical' else None,  # financial_impact
                scenario['root_cause'],
                scenario['category'],
                ['seasonal_pattern', 'training_data_gap', 'deployment_issue'],  # contributing_factors
                scenario['responsible'],
                assigned_to,
                f"Remediation plan: Retrain model with additional data and deploy hotfix.",
                remediation_status,
                remediation_completed,
                self.user_ids['developer_1'] if remediation_completed else None,
                auditor_signoff_date,
                auditor if auditor_signoff_date else None,
                "Reviewed remediation. Model performance restored. Incident closed." if auditor_signoff_date else None,
                scenario['severity'] == 'critical',  # reported_to_regulator
                detected_date + timedelta(days=1) if scenario['severity'] == 'critical' else None,
                f"MAS-CASE-{random.randint(10000, 99999)}" if scenario['severity'] == 'critical' else None,
                datetime.now(),
                datetime.now()
            ))

        insert_query = """
            INSERT INTO failure_incidents (
                incident_id, model_id, failure_type, severity, description,
                detected_date, detected_by, affected_transaction_count,
                false_positive_count, false_negative_count, financial_impact,
                root_cause, root_cause_category, contributing_factors,
                responsible_party, assigned_to, remediation_plan, remediation_status,
                remediation_completed_date, remediation_verified_by,
                auditor_signoff_date, auditor_signoff_by, auditor_notes,
                reported_to_regulator, regulator_report_date, regulator_case_id,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
        """
        execute_batch(self.cur, insert_query, incidents_data)
        self.conn.commit()
        print(f"Generated {len(incidents_data)} failure incidents.")

    def generate_all(self, num_transactions: int = 10000):
        """Generate complete synthetic dataset."""
        print("="*80)
        print("AFAAP Synthetic Dataset Generation")
        print("="*80)

        self.connect()

        try:
            self.get_role_ids()
            self.generate_users()
            self.generate_models()
            self.generate_transactions(num_transactions=num_transactions)
            self.generate_decisions(coverage=0.8)
            self.generate_revalidation_workflows()
            self.generate_failure_incidents()

            # Refresh materialized views (non-concurrent for initial load)
            print("\nRefreshing materialized views...")
            self.cur.execute("REFRESH MATERIALIZED VIEW model_performance_summary;")
            self.cur.execute("REFRESH MATERIALIZED VIEW fairness_metrics_by_type;")
            self.cur.execute("REFRESH MATERIALIZED VIEW fairness_metrics_by_geography;")
            self.cur.execute("REFRESH MATERIALIZED VIEW officer_workload_summary;")
            self.conn.commit()
            print("Materialized views refreshed.")

            print("\n" + "="*80)
            print("Dataset generation complete!")
            print("="*80)
            self._print_summary()

        except Exception as e:
            print(f"Error during generation: {e}")
            self.conn.rollback()
            raise

        finally:
            self.disconnect()

    def _print_summary(self):
        """Print dataset summary statistics."""
        self.cur.execute("SELECT COUNT(*) FROM users;")
        print(f"Users: {self.cur.fetchone()[0]}")

        self.cur.execute("SELECT COUNT(*) FROM models;")
        print(f"Models: {self.cur.fetchone()[0]}")

        self.cur.execute("SELECT COUNT(*) FROM transactions;")
        print(f"Transactions: {self.cur.fetchone()[0]}")

        self.cur.execute("SELECT COUNT(*) FROM decisions;")
        print(f"Decisions: {self.cur.fetchone()[0]}")

        self.cur.execute("SELECT COUNT(*) FROM revalidation_workflows;")
        print(f"Revalidation Workflows: {self.cur.fetchone()[0]}")

        self.cur.execute("SELECT COUNT(*) FROM failure_incidents;")
        print(f"Failure Incidents: {self.cur.fetchone()[0]}")

        self.cur.execute("SELECT COUNT(*) FROM audit_trails;")
        print(f"Audit Trail Records: {self.cur.fetchone()[0]}")

        # Audit completion rate
        self.cur.execute("""
            SELECT
                ROUND(
                    COUNT(CASE WHEN audit_trail_complete THEN 1 END)::NUMERIC / COUNT(*) * 100,
                    2
                ) AS completion_rate
            FROM decisions;
        """)
        print(f"Audit Trail Completion Rate: {self.cur.fetchone()[0]}%")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate synthetic AFAAP dataset')
    parser.add_argument(
        '--transactions',
        type=int,
        default=10000,
        help='Number of transactions to generate (default: 10000)'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default=DATABASE_URL,
        help='PostgreSQL database URL'
    )

    args = parser.parse_args()

    generator = SyntheticDataGenerator(database_url=args.database_url)
    generator.generate_all(num_transactions=args.transactions)
