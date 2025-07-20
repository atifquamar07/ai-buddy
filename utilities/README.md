# Utilities Module

**Author:** Nishant Sharma (nishant@insituate.ai)

This module provides utility files for various functionalities across the application, organized to prevent circular dependencies and promote code reuse.

## Structure

```
utilities/
├── core_utils.py  # Shared logic across all utility files
├── utils.py       # General-purpose utility functions
├── llm_utils.py   # Utility functions specific to language models (LLMs)
└── db_utils.py    # Utility functions related to database operations
```

### 1. `core_utils.py`

**Description:** Implements functions with shared logic across all other utility files.

### 2. `utils.py`

**Description:** Contains general-purpose utility functions used throughout the application.

### 3. `llm_utils.py`

**Description:** Implements utility functions specific to working with language models (LLMs).

### 4. `db_utils.py`

**Description:** Contains utility functions related to database operations.

## Usage

Import utility functions as needed:

```python
from utilities.core_utils import shared_logic
from utilities.db_utils import db_specific_function
from utilities.llm_utils import llm_specific_function
from utilities.utils import general_function
```

## Contributing

Add new functions to the appropriate module and update this `README.md` as necessary.

## License

This project is licensed under the MIT License - see the LICENSE file for details.