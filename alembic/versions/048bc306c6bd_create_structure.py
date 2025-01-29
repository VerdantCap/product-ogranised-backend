"""create structure

Revision ID: 048bc306c6bd
Revises: 
Create Date: 2025-01-29 16:49:04.102165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '048bc306c6bd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First create users table without the workspace foreign key
    op.create_table('users',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=True),
    sa.Column('country', sa.String(), nullable=True),
    sa.Column('city', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('avatar_url', sa.String(), nullable=True),
    sa.Column('google_sub', sa.String(), nullable=True),
    sa.Column('apple_sub', sa.String(), nullable=True),
    sa.Column('oauth_provider', sa.String(), nullable=True),
    sa.Column('is_email_verified', sa.Boolean(), nullable=False),
    sa.Column('email_notification', sa.Boolean(), nullable=False),
    sa.Column('sms_notification', sa.Boolean(), nullable=False),
    sa.Column('push_notification', sa.Boolean(), nullable=False),
    sa.Column('active_workspace_id', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('apple_sub'),
    sa.UniqueConstraint('google_sub')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_name'), 'users', ['name'], unique=False)

    # Then create workspaces table
    op.create_table('workspaces',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('owner_id', sa.String(), nullable=False),
    sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('stripe_id', sa.String(), nullable=False),
    sa.Column('spaces_order', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspaces_id'), 'workspaces', ['id'], unique=False)

    # Now add the foreign key constraint to users table
    op.create_foreign_key(
        'fk_users_active_workspace_id_workspaces',
        'users',
        'workspaces',
        ['active_workspace_id'],
        ['id']
    )

    # Create remaining tables
    op.create_table('events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('workspace_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('start_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
    op.create_table('files',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('path', sa.String(), nullable=False),
    sa.Column('type', sa.Enum('CERTIFICATE', 'POLICY', 'PASSPORT', 'VISA', 'MOT', 'SERVICES', 'TAX', 'PHOTO', 'QUOTE', name='filetype'), nullable=False),
    sa.Column('folder', sa.String(), nullable=False),
    sa.Column('category', sa.String(), nullable=False),
    sa.Column('owner_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_files_id'), 'files', ['id'], unique=False)
    op.create_table('items',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('space', sa.Enum('INSURANCE', 'HOUSEHOLD', 'FINANCE', 'PETS', 'PERSONAL_DOCUMENTS', 'VEHICLES', 'TRAVEL', 'SPECIAL_EVENTS', name='itemspace'), nullable=False),
    sa.Column('type', sa.Enum('CAR_INSURANCE', 'HOME_INSURANCE', 'LIFE_INSURANCE', 'PET_INSURANCE', 'TRAVEL_INSURANCE', 'UTILITIES', 'COUNCIL_TAX', 'BROADBAND', 'MOBILE_PHONE', 'MORTGAGE', 'CREDIT_CARD', 'SAVINGS', 'PENSION', 'VEHICLE_FINANCE', 'CURRENT_ACCOUNT', 'ANIMAL', 'HOLIDAY', 'VISA', 'PASSPORT', 'CAR', 'MOTORBIKE', 'COMMERCIAL_VEHICLE', 'OTHER_VEHICLE', 'BIRTHDAY_PARTY', 'DINNER_PARTY', 'CHRISTENING', 'WEDDING', 'FUNERAL', name='itemtype'), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('workspace_id', sa.String(), nullable=False),
    sa.Column('owner_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_items_id'), 'items', ['id'], unique=False)
    op.create_table('tasks',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('workspace_id', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('owner_id', sa.String(), nullable=False),
    sa.Column('assignee_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_table('user_workspace',
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('workspace_id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'workspace_id')
    )
    op.create_table('accommodations',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('item_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('booking_ref', sa.String(), nullable=True),
    sa.Column('provider', sa.String(), nullable=True),
    sa.Column('arrival_date', sa.Date(), nullable=False),
    sa.Column('departure_date', sa.Date(), nullable=False),
    sa.Column('contact_number', sa.String(), nullable=True),
    sa.Column('contact_email', sa.String(), nullable=True),
    sa.Column('food_drink_included', sa.Boolean(), nullable=True),
    sa.Column('total_cost', sa.Float(), nullable=True),
    sa.Column('deposit_paid', sa.Boolean(), nullable=False),
    sa.Column('deposit_amount', sa.Float(), nullable=True),
    sa.Column('deposit_date', sa.Date(), nullable=True),
    sa.Column('remaining_balance', sa.Float(), nullable=True),
    sa.Column('balance_due_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('attachments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accommodations_id'), 'accommodations', ['id'], unique=False)
    op.create_table('excursions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('item_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('booking_ref', sa.String(), nullable=True),
    sa.Column('provider', sa.String(), nullable=True),
    sa.Column('excursion_date', sa.Date(), nullable=True),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('contact_number', sa.String(), nullable=True),
    sa.Column('contact_email', sa.String(), nullable=True),
    sa.Column('total_cost', sa.Float(), nullable=True),
    sa.Column('deposit_paid', sa.Boolean(), nullable=True),
    sa.Column('deposit_amount', sa.Float(), nullable=True),
    sa.Column('deposit_date', sa.Date(), nullable=True),
    sa.Column('remaining_balance', sa.Float(), nullable=True),
    sa.Column('balance_due_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('attachments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_excursions_id'), 'excursions', ['id'], unique=False)
    op.create_table('item_association',
    sa.Column('item_id', sa.String(), nullable=True),
    sa.Column('related_item_id', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], ),
    sa.ForeignKeyConstraint(['related_item_id'], ['items.id'], )
    )
    op.create_table('transports',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('item_id', sa.String(), nullable=False),
    sa.Column('transport_mode', sa.String(), nullable=False),
    sa.Column('trip_type', sa.String(), nullable=False),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transports_id'), 'transports', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_transports_id'), table_name='transports')
    op.drop_table('transports')
    op.drop_table('item_association')
    op.drop_index(op.f('ix_excursions_id'), table_name='excursions')
    op.drop_table('excursions')
    op.drop_index(op.f('ix_accommodations_id'), table_name='accommodations')
    op.drop_table('accommodations')
    op.drop_table('user_workspace')
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
    op.drop_index(op.f('ix_items_id'), table_name='items')
    op.drop_table('items')
    op.drop_index(op.f('ix_files_id'), table_name='files')
    op.drop_table('files')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_table('events')
    op.drop_index(op.f('ix_workspaces_id'), table_name='workspaces')
    op.drop_table('workspaces')
    op.drop_index(op.f('ix_users_name'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
