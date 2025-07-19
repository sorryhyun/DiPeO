# Entity Definition Examples

This document provides example entity definitions for the DiPeO entity-based code generation system. These examples demonstrate various patterns and features available when defining entities.

## Basic Entity Definition

A minimal entity with basic CRUD operations:

```typescript
import { defineEntity } from '../entity-config';

export const ProductEntity = defineEntity({
  name: 'Product',
  plural: 'products',
  
  fields: {
    id: {
      type: 'ProductID',
      generated: true,
      required: true
    },
    name: {
      type: 'string',
      required: true,
      validation: {
        minLength: 1,
        maxLength: 100
      }
    },
    price: {
      type: 'number',
      required: true,
      validation: {
        min: 0
      }
    },
    description: {
      type: 'string',
      nullable: true
    },
    isActive: {
      type: 'boolean',
      default: true
    }
  },
  
  operations: {
    create: true,
    update: true,
    delete: true,
    list: true,
    get: true
  }
});
```

## Entity with Relations

Example showing different relation types:

```typescript
export const BlogPostEntity = defineEntity({
  name: 'BlogPost',
  plural: 'blogPosts',
  
  fields: {
    id: {
      type: 'BlogPostID',
      generated: true,
      required: true
    },
    title: {
      type: 'string',
      required: true,
      validation: {
        minLength: 5,
        maxLength: 200
      }
    },
    content: {
      type: 'string',
      required: true,
      validation: {
        minLength: 10,
        maxLength: 10000
      }
    },
    publishedAt: {
      type: 'Date',
      nullable: true
    },
    createdAt: {
      type: 'Date',
      generated: true
    },
    updatedAt: {
      type: 'Date',
      generated: true
    }
  },
  
  relations: {
    author: {
      type: 'Person',
      relation: 'many-to-one',  // Many posts to one author
      required: true
    },
    tags: {
      type: 'Tag',
      relation: 'many-to-many'  // Many posts can have many tags
    },
    featuredImage: {
      type: 'Image',
      relation: 'one-to-one',   // One post has one featured image
      required: false
    }
  },
  
  operations: {
    create: {
      input: ['title', 'content', 'authorId', 'tagIds'],
      returnEntity: true
    },
    update: {
      input: ['title', 'content', 'publishedAt', 'tagIds'],
      partial: true
    },
    list: {
      filters: ['authorId', 'publishedAt', 'tagIds'],
      sortable: ['publishedAt', 'createdAt', 'title'],
      pagination: true,
      defaultPageSize: 10
    },
    get: {
      include: ['author', 'tags', 'featuredImage']
    }
  },
  
  features: {
    timestamps: true,
    softDelete: true
  }
});
```

## Entity with Custom Operations

Example with custom business logic operations:

```typescript
export const ShoppingCartEntity = defineEntity({
  name: 'ShoppingCart',
  plural: 'shoppingCarts',
  
  fields: {
    id: {
      type: 'ShoppingCartID',
      generated: true,
      required: true
    },
    userId: {
      type: 'UserID',
      required: true
    },
    status: {
      type: 'string',
      default: 'active',
      validation: {
        pattern: '^(active|abandoned|checked_out)$'
      }
    },
    total: {
      type: 'number',
      default: 0,
      validation: {
        min: 0
      }
    },
    itemCount: {
      type: 'number',
      default: 0
    },
    createdAt: {
      type: 'Date',
      generated: true
    },
    updatedAt: {
      type: 'Date',
      generated: true
    }
  },
  
  relations: {
    items: {
      type: 'CartItem',
      relation: 'one-to-many',
      inverse: 'cart'
    }
  },
  
  operations: {
    create: {
      input: ['userId'],
      customLogic: `
        # Ensure user doesn't already have an active cart
        existing_cart = await cart_service.find_active_by_user(input.user_id)
        if existing_cart:
            raise ValueError("User already has an active cart")
      `
    },
    
    get: {
      include: ['items'],
      throwIfNotFound: true
    },
    
    custom: {
      addItem: {
        name: 'addItemToCart',
        type: 'mutation',
        input: ['cartId', 'productId', 'quantity'],
        returns: 'ShoppingCart',
        implementation: `
          cart = await cart_service.get(cart_id)
          if not cart:
              raise ValueError("Cart not found")
          
          # Check product availability
          product = await product_service.get(product_id)
          if not product or not product.is_active:
              raise ValueError("Product not available")
          
          # Add or update item
          await cart_service.add_item(
              cart_id=cart_id,
              product_id=product_id,
              quantity=quantity,
              price=product.price
          )
          
          # Recalculate total
          await cart_service.recalculate_total(cart_id)
          
          return await cart_service.get(cart_id, include_items=True)
        `
      },
      
      checkout: {
        name: 'checkoutCart',
        type: 'mutation',
        input: ['cartId', 'paymentMethodId'],
        returns: 'Order',
        implementation: `
          cart = await cart_service.get(cart_id, include_items=True)
          if not cart:
              raise ValueError("Cart not found")
          
          if cart.item_count == 0:
              raise ValueError("Cannot checkout empty cart")
          
          # Create order from cart
          order = await order_service.create_from_cart(
              cart=cart,
              payment_method_id=payment_method_id
          )
          
          # Mark cart as checked out
          cart.status = "checked_out"
          await cart_service.update(cart)
          
          return order
        `
      }
    }
  },
  
  features: {
    timestamps: true,
    cache: true,
    cacheTTL: 300  // 5 minutes
  },
  
  service: {
    name: 'cart_service',
    async: true,
    dependencies: ['product_service', 'order_service']
  }
});
```

## Entity with Advanced Features

Example showing validation, audit, and caching features:

```typescript
export const UserAccountEntity = defineEntity({
  name: 'UserAccount',
  plural: 'userAccounts',
  
  fields: {
    id: {
      type: 'UserAccountID',
      generated: true,
      required: true
    },
    email: {
      type: 'string',
      required: true,
      unique: true,
      validation: {
        pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
        custom: 'validate_email_not_disposable'
      }
    },
    username: {
      type: 'string',
      required: true,
      unique: true,
      validation: {
        minLength: 3,
        maxLength: 30,
        pattern: '^[a-zA-Z0-9_]+$'
      }
    },
    passwordHash: {
      type: 'string',
      required: true,
      hidden: true  // Never exposed in API
    },
    isVerified: {
      type: 'boolean',
      default: false
    },
    verificationToken: {
      type: 'string',
      nullable: true,
      hidden: true
    },
    lastLoginAt: {
      type: 'Date',
      nullable: true
    },
    loginAttempts: {
      type: 'number',
      default: 0
    },
    lockedUntil: {
      type: 'Date',
      nullable: true
    },
    preferences: {
      type: 'JSON',
      default: {},
      validation: {
        custom: 'validate_preferences_schema'
      }
    },
    createdAt: {
      type: 'Date',
      generated: true
    },
    updatedAt: {
      type: 'Date',
      generated: true
    }
  },
  
  operations: {
    create: {
      input: ['email', 'username', 'password'],
      customLogic: `
        # Hash password
        input['password_hash'] = await auth_service.hash_password(input.password)
        del input['password']
        
        # Generate verification token
        input['verification_token'] = generate_secure_token()
        
        # Send verification email
        await email_service.send_verification_email(
            email=input.email,
            token=input.verification_token
        )
      `
    },
    
    update: {
      input: ['email', 'username', 'preferences'],
      partial: true,
      customLogic: `
        # If email is being changed, require re-verification
        if 'email' in updates and updates['email'] != entity.email:
            updates['is_verified'] = False
            updates['verification_token'] = generate_secure_token()
            
            await email_service.send_verification_email(
                email=updates['email'],
                token=updates['verification_token']
            )
      `
    },
    
    delete: {
      soft: true,
      customLogic: `
        # Archive user data before soft delete
        await archive_service.archive_user_data(entity.id)
        
        # Cancel any active subscriptions
        await subscription_service.cancel_all_for_user(entity.id)
      `
    },
    
    list: {
      filters: ['isVerified', 'createdAt', 'lastLoginAt'],
      sortable: ['username', 'email', 'createdAt', 'lastLoginAt'],
      pagination: true,
      defaultPageSize: 50,
      maxPageSize: 200,
      adminOnly: true  // Requires admin role
    },
    
    get: {
      throwIfNotFound: true,
      customLogic: `
        # Users can only get their own account unless admin
        if not context.is_admin and entity.id != context.user_id:
            raise PermissionError("Cannot access other user accounts")
      `
    },
    
    custom: {
      verifyEmail: {
        name: 'verifyEmail',
        type: 'mutation',
        input: ['token'],
        returns: 'UserAccount',
        implementation: `
          user = await user_service.find_by_verification_token(token)
          if not user:
              raise ValueError("Invalid verification token")
          
          user.is_verified = True
          user.verification_token = None
          
          return await user_service.update(user)
        `
      },
      
      changePassword: {
        name: 'changePassword',
        type: 'mutation',
        input: ['userId', 'currentPassword', 'newPassword'],
        returns: 'Boolean',
        implementation: `
          user = await user_service.get(user_id)
          if not user:
              raise ValueError("User not found")
          
          # Verify current password
          if not await auth_service.verify_password(current_password, user.password_hash):
              raise ValueError("Current password is incorrect")
          
          # Update password
          user.password_hash = await auth_service.hash_password(new_password)
          await user_service.update(user)
          
          # Send notification
          await email_service.send_password_changed_notification(user.email)
          
          return True
        `
      }
    }
  },
  
  features: {
    timestamps: true,
    softDelete: true,
    audit: true,       // Track all changes
    cache: true,
    cacheTTL: 600,     // 10 minutes
    versioning: true   // Keep version history
  },
  
  service: {
    name: 'user_service',
    async: true,
    dependencies: ['auth_service', 'email_service', 'archive_service', 'subscription_service']
  }
});
```

## Field Types Reference

### Basic Types
- `string` - Text values
- `number` - Numeric values (integers or decimals)
- `boolean` - True/false values
- `Date` - Date/datetime values
- `JSON` - Arbitrary JSON data

### Branded ID Types
- Custom ID types (e.g., `UserID`, `ProductID`)
- Always use with `generated: true`

### Field Options
- `required: true` - Field must be provided
- `nullable: true` - Field can be null
- `unique: true` - Field must be unique across all entities
- `hidden: true` - Field is never exposed in API
- `generated: true` - Field is auto-generated by the system
- `default: value` - Default value for the field

### Validation Options
- `minLength` / `maxLength` - String length constraints
- `min` / `max` - Numeric value constraints
- `pattern` - Regex pattern for validation
- `custom` - Name of custom validation function

## Relation Types

- `one-to-one` - One entity relates to exactly one other entity
- `one-to-many` - One entity relates to many other entities
- `many-to-one` - Many entities relate to one other entity
- `many-to-many` - Many entities relate to many other entities

## Operation Types

### Standard Operations
- `create` - Create new entities
- `update` - Update existing entities
- `delete` - Delete entities (soft or hard)
- `list` - List entities with filtering/sorting/pagination
- `get` - Get a single entity by ID

### Custom Operations
Define any custom mutations or queries specific to your entity's business logic.

## Best Practices

1. **Use Branded IDs**: Always use specific ID types (e.g., `UserID` not just `ID`)
2. **Enable Timestamps**: Use `timestamps: true` for audit trails
3. **Soft Delete**: Prefer soft deletes for data retention
4. **Validation**: Add appropriate validation rules to ensure data integrity
5. **Relations**: Define both sides of relationships when possible
6. **Service Dependencies**: Explicitly declare service dependencies
7. **Error Handling**: Provide clear error messages in custom logic
8. **Security**: Implement proper access control in custom logic
9. **Caching**: Enable caching for frequently accessed entities
10. **Documentation**: Comment complex custom logic for maintainability