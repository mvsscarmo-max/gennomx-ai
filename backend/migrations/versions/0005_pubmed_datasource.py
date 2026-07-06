"""Add pubmed data_source entry.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-23
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO data_sources (id, name, slug, category, access_method, official_url, api_url,
                                   license_status, update_frequency, connector_status, is_enabled,
                                   created_at, updated_at)
        VALUES
          (gen_random_uuid(), 'PubMed', 'pubmed', 'scientific', 'api',
           'https://pubmed.ncbi.nlm.nih.gov',
           'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/',
           'open', 'daily', 'inactive', false, now(), now())
        ON CONFLICT (slug) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("DELETE FROM data_sources WHERE slug = 'pubmed'")
