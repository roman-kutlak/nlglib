#  * This features determines if a pronominal verb complement phrase is a
#  * clitic. Clitic phrases are realised before the verb instead of behind it.
#  * The verb phrase syntax syntax methods determine the exact position.
#  * </p>
#  * <table border="1">
#  * <tr>
#  * <td><b>Feature name</b></td>
#  * <td><em>clitic</em></td>
#  * </tr>
#  * <tr>
#  * <td><b>Expected type</b></td>
#  * <td><code>Boolean</code></td>
#  * </tr>
#  * <tr>
#  * <td><b>Created by</b></td>
#  * <td>The verb phrase syntax syntax methods set this flag on pronominal
#  * verb complement phrases.</td>
#  * </tr>
#  * <tr>
#  * <td><b>Used by</b></td>
#  * <td>The verb phrase syntax syntax methods to correctly place pronominal
#  * verb complements.</td>
#  * </tr>
#  * <tr>
#  * <td><b>Applies to</b></td>
#  * <td>Pronominal verb complement phrases.</td>
#  * </tr>
#  * <tr>
#  * <td><b>Default</b></td>
#  * <td><code>Boolean.FALSE</code></td>
#  * </tr>
#  * </table>
#
CLITIC = "clitic"

#
#  * <p>
#  * This features indicates that the phrase is replaced by a relative pronoun
#  * somewhere and that therefore it must not be realised. It is only used
#  * with preposition phrases, as the relative clause may not be their parent.
#  * </p>
#  * <table border="1">
#  * <tr>
#  * <td><b>Feature name</b></td>
#  * <td><em>relativised</em></td>
#  * </tr>
#  * <tr>
#  * <td><b>Expected type</b></td>
#  * <td><code>Boolean</code></td>
#  * </tr>
#  * <tr>
#  * <td><b>Created by</b></td>
#  * <td>The clause syntax syntax methods set this flag on relative phrases
#  * that are preposition phrases.</td>
#  * </tr>
#  * <tr>
#  * <td><b>Used by</b></td>
#  * <td>The generic phrase syntax syntax methods to determine if a phrase
#  * must be realised.</td>
#  * </tr>
#  * <tr>
#  * <td><b>Applies to</b></td>
#  * <td>Preposition phrases.</td>
#  * </tr>
#  * <tr>
#  * <td><b>Default</b></td>
#  * <td><code>Boolean.FALSE</code></td>
#  * </tr>
#  * </table>
#
RELATIVISED = "relativised"
