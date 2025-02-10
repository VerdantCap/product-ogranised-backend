# Project Description

## API Endpoints and Functionality

### Authentication Controller (`auth_controller.py`)
- **register_controller**: Handles user registration by accepting user details and creating a new user account.
- **login_controller**: Manages user login by verifying credentials and issuing authentication tokens.
- **google_login**: Redirects users to Google's OAuth for authentication.
- **login_callback_controller**: Processes the callback from Google OAuth and logs the user in.
- **logout_controller**: Logs the user out by invalidating the session or token.
- **verify_user_email_controller**: Sends a verification email to the user and verifies the email address.
- **verify_otp_controller**: Verifies the OTP sent to the user for authentication purposes.
- **forgot_password_controller**: Initiates the password reset process by sending a reset link or OTP.
- **verify_otp_forgot_password_controller**: Verifies the OTP for password reset.
- **update_password_controller**: Updates the user's password after verification.
- **replace_password_controller**: Replaces the user's password with a new one.
- **delete_user_controller**: Deletes a user account from the system.
- **refresh_token_controller**: Refreshes the authentication token to extend the session.

### Event Controller (`event_controller.py`)
- **list_events**: Retrieves a list of all events available in the system.
- **create_event**: Creates a new event with specified details.
- **get_event**: Retrieves details of a specific event by its ID.
- **update_event**: Updates the details of an existing event.
- **delete_event**: Deletes an event from the system.
- **get_upcoming_events**: Retrieves a list of upcoming events based on the current date.

### Item Controller (`item_controller.py`)
- **GET /list-user**: Lists items owned by the current user.
- **GET /list-space**: Lists items by space.
- **GET /list-type**: Lists items by type.
- **GET /list-status**: Lists items by status.
- **GET /list-workspace**: Lists items by workspace.
- **GET /list-workspace-and-user**: Lists items by workspace and user.
- **GET /list-all**: Lists all items.
- **POST /create**: Creates a new item.
- **PUT /{item_id}/update**: Updates an existing item.
- **DELETE /{item_id}/delete**: Deletes an item.
- **POST /soft-delete**: Soft deletes an item.
- **POST /{item_id}/upload**: Adds a file to an item.
- **POST /{item_id}/transport**: Creates a transport entry for an item.
- **GET /{item_id}/transport/{transport_id}**: Updates a transport entry.
- **POST /{item_id}/accommodation/create**: Creates an accommodation entry.
- **PUT /{item_id}/accommodation/{accommodation_id}/update**: Updates an accommodation entry.
- **POST /{item_id}/excursion/create**: Creates an excursion entry.
- **PUT /{item_id}/excursions/{excursion_id}/update**: Updates an excursion entry.
- **POST /{item_id}/related/{related_id}**: Adds a related item.
- **DELETE /{item_id}/related/{related_id}**: Removes a related item.

### Workspace Controller (`workspace_controller.py`)
- **create_workspace**: Creates a new workspace with specified details.
- **manage_workspace**: Manages workspace settings and configurations.
- **update_workspace**: Updates the details of an existing workspace.
- **delete_workspace**: Deletes a workspace from the system.
- **renewal_required**: Checks if a workspace subscription renewal is required.
- **refresh_spaces**: Refreshes the spaces within a workspace.
- **update_item_space_order**: Updates the order of items within a space.
- **toggle_space**: Toggles the visibility or status of a space.
- **maintain_subscription**: Maintains the subscription status of a workspace.
- **cancel_subscription**: Cancels the subscription for a workspace.
- **set_active_workspace**: Sets a workspace as active for the user.
- **list_members**: Lists all members within a workspace.
- **add_member**: Adds a new member to a workspace.

## Database Schemas and Relationships

### Item Model
- **Table Name**: `items`
- **Columns**:
  - `id`: Primary key, string type.
  - `space`: Enum type, representing the space of the item.
  - `type`: Enum type, representing the type of the item.
  - `description`: Optional string, providing a description of the item.
  - `fields`: JSONB type, storing additional fields as a dictionary.
  - `start_at`: DateTime, defaulting to the current time, representing the start time.
  - `end_at`: Optional DateTime, representing the end time.
  - `workspace_id`: Foreign key referencing `workspaces.id`, with cascade on delete and update.
  - `owner_id`: Foreign key referencing `users.id`, with cascade on delete and update.

- **Relationships**:
  - `workspace`: Relationship to the `Workspace` model, back-populated by `items`.
  - `owner`: Relationship to the `User` model, back-populated by `items`.
  - `transports`: Relationship to the `Transport` model, back-populated by `items`.
  - `accommodations`: Relationship to the `Accommodation` model, back-populated by `items`.
  - `excursions`: Relationship to the `Excursion` model, back-populated by `items`.
  - `related_items`: Self-referential many-to-many relationship through `item_association`, allowing items to be related to other items.

### Accommodation Model
- **Table Name**: `accommodations`
- **Columns**:
  - `id`: Primary key, string type.
  - `item_id`: Foreign key referencing `items.id`, with cascade on delete and update.
  - `name`: String, representing the name of the accommodation.
  - `booking_ref`: Optional string, representing the booking reference.
  - `provider`: Optional string, representing the provider of the accommodation.
  - `arrival_date`: Date, representing the arrival date.
  - `departure_date`: Date, representing the departure date.
  - `contact_number`: Optional string, representing the contact number.
  - `contact_email`: Optional string, representing the contact email.
  - `food_drink_included`: Boolean, indicating if food and drink are included.
  - `total_cost`: Float, representing the total cost of the accommodation.
  - `deposit_paid`: Boolean, indicating if the deposit has been paid.
  - `deposit_amount`: Float, representing the deposit amount.
  - `deposit_date`: Optional date, representing the deposit date.
  - `remaining_balance`: Float, representing the remaining balance.
  - `balance_due_date`: Optional date, representing the balance due date.
  - `notes`: Optional text, providing additional notes.
  - `attachments`: JSONB, storing attachments as a list.

- **Relationships**:
  - `items`: Relationship to the `Item` model, back-populated by `accommodations`.

### Event Model
- **Table Name**: `events`
- **Columns**:
  - `id`: Primary key, string type.
  - `workspace_id`: Foreign key referencing `workspaces.id`, with cascade on delete and update.
  - `name`: String, representing the name of the event.
  - `description`: Optional string, providing a description of the event.
  - `start_at`: Optional DateTime, representing the start time of the event.
  - `end_at`: Optional DateTime, representing the end time of the event.

- **Relationships**:
  - `workspace`: Relationship to the `Workspace` model, back-populated by `event`.

### Excursion Model
- **Table Name**: `excursions`
- **Columns**:
  - `id`: Primary key, string type.
  - `item_id`: Foreign key referencing `items.id`, with cascade on delete and update.
  - `name`: String, representing the name of the excursion.
  - `booking_ref`: Optional string, representing the booking reference.
  - `provider`: Optional string, representing the provider of the excursion.
  - `excursion_date`: Optional date, representing the date of the excursion.
  - `start_time`: Optional DateTime, representing the start time of the excursion.
  - `end_time`: Optional DateTime, representing the end time of the excursion.
  - `contact_number`: Optional string, representing the contact number.
  - `contact_email`: Optional string, representing the contact email.
  - `total_cost`: Float, representing the total cost of the excursion.
  - `deposit_paid`: Boolean, indicating if the deposit has been paid.
  - `deposit_amount`: Float, representing the deposit amount.
  - `deposit_date`: Optional date, representing the deposit date.
  - `remaining_balance`: Float, representing the remaining balance.
  - `balance_due_date`: Optional date, representing the balance due date.
  - `notes`: Optional text, providing additional notes.
  - `attachments`: JSONB, storing attachments as a list.

- **Relationships**:
  - `items`: Relationship to the `Item` model, back-populated by `excursions`.

### FailedJob Model
- **Table Name**: `failed_jobs`
- **Columns**:
  - `id`: Primary key, string type.
  - `connection`: Text, representing the connection details.
  - `queue`: Text, representing the queue name.
  - `payload`: Text, representing the job payload.
  - `exception`: Text, representing the exception message.
  - `failed_at`: DateTime, defaulting to the current time, representing when the job failed.

### File Model
- **Table Name**: `files`
- **Columns**:
  - `id`: Primary key, string type.
  - `path`: String, representing the file path.
  - `type`: Enum type, representing the file type.
  - `folder`: String, representing the folder name.
  - `category`: String, representing the file category.
  - `owner_id`: Foreign key referencing `users.id`, with cascade on delete and update.

- **Relationships**:
  - `owner`: Relationship to the `User` model, back-populated by `files`.

- **Methods**:
  - `delete_file`: Deletes the physical file from storage and removes the database record.

### Job Model
- **Table Name**: `jobs`
- **Columns**:
  - `id`: Primary key, string type.
  - `queue`: String, representing the queue name.
  - `payload`: Text, representing the job payload.
  - `attempts`: Integer, representing the number of attempts made to process the job.
  - `reserved_at`: Optional DateTime, representing when the job was reserved.
  - `available_at`: DateTime, representing when the job becomes available for processing.
  - `created_at`: Integer, representing the timestamp when the job was created.

### JobBatch Model
- **Table Name**: `job_batches`
- **Columns**:
  - `id`: Primary key, string type.
  - `name`: String, representing the name of the job batch.
  - `total_jobs`: Integer, representing the total number of jobs in the batch.
  - `pending_jobs`: Integer, representing the number of pending jobs.
  - `failed_jobs`: Integer, representing the number of failed jobs.
  - `failed_job_ids`: List of strings, representing the IDs of failed jobs.
  - `options`: JSONB, storing additional options as a JSON object.
  - `cancelled_at`: Optional DateTime, representing when the batch was cancelled.
  - `created_at`: DateTime, defaulting to the current time, representing when the batch was created.
  - `finished_at`: Optional DateTime, representing when the batch was finished.

### Task Model
- **Table Name**: `tasks`
- **Columns**:
  - `id`: Primary key, string type.
  - `workspace_id`: Foreign key referencing `workspaces.id`, with cascade on delete and update.
  - `title`: String, representing the title of the task.
  - `due_at`: Optional DateTime, representing the due date and time of the task.
  - `description`: Text, providing a detailed description of the task.
  - `completed_at`: Optional DateTime, representing when the task was completed.
  - `assignee_id`: Foreign key referencing `users.id`, with cascade on delete and update.

- **Relationships**:
  - `assignee`: Relationship to the `User` model, back-populated by `tasks`.

- **Methods**:
  - `is_completed`: Returns a boolean indicating if the task is completed.
  - `reset`: Resets the task to an incomplete state.
  - `complete`: Marks the task as completed.
  - `get_todo_tasks`: Class method that returns tasks that are not completed.
  - `assigned_to`: Class method that returns tasks assigned to a specific user or where the assignee is null.

### Transport Model
- **Table Name**: `transports`
- **Columns**:
  - `id`: Primary key, string type.
  - `item_id`: Foreign key referencing `items.id`, with cascade on delete and update.
  - `transport_mode`: String, representing the mode of transport.
  - `trip_type`: String, representing the type of trip.
  - `details`: JSONB, storing additional details as a JSON object.

- **Relationships**:
  - `items`: Relationship to the `Item` model, back-populated by `transports`.

### User Model
- **Table Name**: `users`
- **Columns**:
  - `id`: Primary key, string type.
  - `name`: String, representing the user's name.
  - `email`: String, unique, representing the user's email.
  - `password`: String, representing the user's password.
  - `country`: String, representing the user's country.
  - `city`: String, representing the user's city.
  - `created_at`: DateTime, defaulting to the current time, representing when the user was created.
  - `updated_at`: Optional DateTime, representing when the user was last updated.
  - `avatar_url`: String, representing the URL of the user's avatar.
  - `oauth_id`: String, representing the OAuth ID.
  - `oauth_driver`: String, representing the OAuth driver.
  - `access_token`: Text, representing the access token.
  - `refresh_token`: Text, representing the refresh token.
  - `token_expires_at`: Optional DateTime, representing when the token expires.
  - `email_notification`: Boolean, indicating if email notifications are enabled.
  - `sms_notification`: Boolean, indicating if SMS notifications are enabled.
  - `push_notification`: Boolean, indicating if push notifications are enabled.
  - `active_workspace_id`: Foreign key referencing `workspaces.id`.

- **Relationships**:
  - `workspaces`: Many-to-many relationship with the `Workspace` model through `user_workspace`.
  - `tasks_owned`: Relationship to the `Task` model for tasks owned by the user.
  - `tasks_assigned`: Relationship to the `Task` model for tasks assigned to the user.
  - `files`: Relationship to the `File` model, back-populated by `owner`.
  - `items`: Relationship to the `Item` model, back-populated by `owner`.

- **Methods**:
  - `is_oauthed`: Hybrid property that returns a boolean indicating if the user is authenticated via OAuth.

### Workspace Model
- **Table Name**: `workspaces`
- **Columns**:
  - `id`: Primary key, string type.
  - `owner_id`: Foreign key referencing `users.id`, with cascade on delete and update.
  - `cancelled_at`: Optional DateTime, representing when the workspace was cancelled.
  - `expires_at`: Optional DateTime, representing when the workspace subscription expires.
  - `stripe_id`: String, representing the Stripe ID for billing purposes.
  - `spaces_order`: JSONB, storing the order of spaces as a JSON array.

- **Relationships**:
  - `users`: Many-to-many relationship with the `User` model through `user_workspace`.
  - `event`: Relationship to the `Event` model, back-populated by `workspace`.
  - `items`: Relationship to the `Item` model, back-populated by `workspace`.

### Models
- **Accommodation**: Represents accommodation-related data.
- **Event**: Represents event-related data.
- **Excursion**: Represents excursion-related data.
- **FailedJob**: Represents failed job records.
- **File**: Represents file-related data, including a method to delete files.
- **Item**: Represents items with various methods to check status and manage files.
- **Job**: Represents job-related data.
- **JobBatch**: Represents batches of jobs.
- **Task**: Represents tasks with methods to manage task completion and assignment.
- **Transport**: Represents transport-related data.
- **User**: Represents user-related data, including OAuth status.
- **Workspace**: Represents workspace-related data.

### Schemas
- **Accommodation Schemas**: Includes `Accommodation`, `AccommodationCreate`, and `AccommodationUpdate` for managing accommodation data.
- **Auth Schemas**: Includes various schemas for user authentication and profile management, such as `UserBase`, `CreateUserIn`, `AccessToken`, and others.
- **Event Schemas**: Includes `Event`, `EventCreate`, and `EventUpdate` for managing event data.
- **Excursion Schemas**: Includes `Excursion`, `ExcursionCreate`, and `ExcursionUpdate` for managing excursion data.
- **File Schemas**: Includes `FileCreate`, `FileUpdate`, and `File` for managing file data.
- **Item Schemas**: Includes `Item`, `ItemCreate`, and `ItemUpdate` for managing item data.
- **Task Schemas**: Includes `Task`, `TaskCreate`, and `TaskUpdate` for managing task data.
- **Transport Schemas**: Includes `TransportBase`, `TransportCreate`, and `TransportUpdate` for managing transport data.
- **Workspace Schemas**: Includes `WorkspaceBase`, `WorkspaceCreate`, and `WorkspaceUpdate` for managing workspace data.

## Configuration

- **Database**: PostgreSQL configured with `SQLALCHEMY_DATABASE_URL`.
- **Redis**: Configured with `REDIS_HOST`, `REDIS_PORT`, and other related settings.
- **Google OIDC**: Configured with `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and related URLs.
- **SMTP**: Configured for email services with `SMTP_SERVER`, `SMTP_PORT`, and credentials.
- **Stripe**: Configured for payment processing with `STRIPE_SECRET` and related settings.
- **JWT**: Configured for authentication with `JWT_SECRET` and `JWT_EXPIRY_DAYS`.
- **OTP**: Configured with `OTP_EXPIRY_MINUTES`.

## To Do
Plz add the opinion about the current structure and something you want.
this is only basic project...