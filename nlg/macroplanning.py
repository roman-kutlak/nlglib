from nlg.structures import RST, Document, Section, Paragraph, Message, MsgSpec


def select_content(messages, workflow, ontology, user_model, domain_history):
    selected = list()
    for msg in messages:
        instance = msg.instantiate(workflow)
        if instance is not None:
            selected.append(instance)

    return selected



