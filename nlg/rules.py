from common.dstruct import Plan

import copy
import itertools


def NoMatchError(Exception):
    pass


def apply_rules(rules, plan):
    """
    Go through the plan and replace sequences of actions by high-level action.
    """
    new_plan = Plan(plan.name, copy.deepcopy(plan.domain),
                    copy.deepcopy(plan.problem), list(),
                    copy.deepcopy(plan.actions))

    i = 0
    while i < plan.length:
        print("\ti: %d in %s" % (i, plan.sequence))
        step = plan.sequence[i]
        action = plan.actions[step]
        replaced = False
        # find matching pattern
        for rule in rules:
            try :
                rule_actions = rule.lhs
                for j in range(len(rule_actions)):
                    rule_action_name = rule_actions[j].name
                    action_name = plan.actions[plan.sequence[i + j]].name
                    print("rule_action_name: %s action_name %s" %
                          (rule_action_name, action_name))
                    if rule_action_name != action_name:
                        raise NoMatchError

            except Exception:
                # rule actions don't match
                print("Rule doesn't match: %s" % rule_actions)
                continue

            else:
                print ("match on inedx %d" % i)
                # we have a potential match (at least the names are matching)
                advance = try_replace_actions(i, rule, plan, new_plan)
                # advance contains the number of actions that were replaced
                if advance > 0:
                    print ("i: %d advanced by %d " % (i, advance))
                    i += advance
                    replaced = True
                    # only apply one rule at a time
                    break

        if not replaced:
            # no rules applied
            new_plan.sequence.append(plan.sequence[i])
            i += 1
    return new_plan


def try_replace_actions(index, rule, old_plan, new_plan):
    """
    Try to replace a sequence of actions in an old plan starting at 'index'
    by a sequence of actions on the rhs of the rule and append it to the 
    new_plan.
    
    """
    # in order to apply the rule, the bindings of variables must match
    bindings = dict()
    length = len(rule.lhs)
    old_action_indices = old_plan.sequence[index: index + length]
    
    for i in range(length):
        plan_action = old_plan.actions[old_action_indices[i]]
        rule_action = rule.lhs[i]
        for param_idx in range(len(plan_action.signature)):
            plan_action_param = plan_action.signature[param_idx]
            rule_action_param = rule_action.signature[param_idx]
            if not add_binding(rule_action_param[0],
                               plan_action_param[0], bindings):
                return 0

    # bindings seem to be fine, add new actions
    old_max = max(old_plan.sequence)
    new_max = -1
    if len(new_plan.sequence) > 0:
        new_max = max(new_plan.sequence)
    max_id = max(old_max, new_max)

    # copy actions
    new_actions = list()
    for a in rule.rhs:
        new_actions.append(copy.deepcopy(a))

    for new_action in new_actions:
        # adjust variable names/bindings
        new_signature = list()
        for param in new_action.signature:
            # as tuples are const, need to use lists to replace the value
            var = list(param)
            var[0] = bindings[param[0]]
            new_signature.append(tuple(var))
        
        new_action.signature = new_signature
        max_id += 1
        new_action.id = max_id
        new_plan.sequence.append(max_id)
        new_plan.actions[max_id] = new_action
        
    return len(rule.lhs)


def add_binding(key, value, bindings):
    if key in bindings.keys():
        return (bindings[key] == value)
    bindings[key] = value
    return True
