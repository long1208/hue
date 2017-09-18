from __future__ import unicode_literals


class MigrationOptimizer(object):
    """
    Powers the optimization process, where you provide a list of Operations
    and you are returned a list of equal or shorter length - operations
    are merged into one if possible.

    For example, a CreateModel and an AddField can be optimized into a
    new CreateModel, and CreateModel and DeleteModel can be optimized into
    nothing.
    """

    def optimize(self, operations, app_label=None):
        """
        Main optimization entry point. Pass in a list of Operation instances,
        get out a new list of Operation instances.

        Unfortunately, due to the scope of the optimization (two combinable
        operations might be separated by several hundred others), this can't be
        done as a peephole optimization with checks/output implemented on
        the Operations themselves; instead, the optimizer looks at each
        individual operation and scans forwards in the list to see if there
        are any matches, stopping at boundaries - operations which can't
        be optimized over (RunSQL, operations on the same field/model, etc.)

        The inner loop is run until the starting list is the same as the result
        list, and then the result is returned. This means that operation
        optimization must be stable and always return an equal or shorter list.

        The app_label argument is optional, but if you pass it you'll get more
        efficient optimization.
        """
        # Internal tracking variable for test assertions about # of loops
        self._iterations = 0
        while True:
            result = self.optimize_inner(operations, app_label)
            self._iterations += 1
            if result == operations:
                return result
            operations = result

    def optimize_inner(self, operations, app_label=None):
        """
        Inner optimization loop.
        """
        new_operations = []
        for i, operation in enumerate(operations):
            # Compare it to each operation after it
            for j, other in enumerate(operations[i + 1:]):
                in_between = operations[i + 1:i + j + 1]
                result = operation.reduce(other, in_between, app_label)
                if isinstance(result, list):
                    # Optimize! Add result, then remaining others, then return
                    new_operations.extend(result)
                    new_operations.extend(in_between)
                    new_operations.extend(operations[i + j + 2:])
                    return new_operations
                if not result:
                    # We can't optimize across `other`.
                    new_operations.append(operation)
                    break
            else:
                new_operations.append(operation)
        return new_operations